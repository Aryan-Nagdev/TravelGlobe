"""Apache Kafka event bus — replaces ad-hoc in-process event handling."""
from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings
from app import hdfs_store

TOPICS = [
    "travel.search",
    "travel.analysis",
    "travel.chat",
    "sar.alerts",
    "sar.assessed",
]

STATS: Dict[str, Any] = {
    "produced": 0,
    "consumed": 0,
    "last_event": None,
    "connected": False,
}

_producer = None
_lock = threading.Lock()


def _bootstrap() -> str:
    return settings.KAFKA_BOOTSTRAP


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    try:
        from kafka import KafkaProducer

        _producer = KafkaProducer(
            bootstrap_servers=_bootstrap(),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            retries=3,
            acks=1,
            request_timeout_ms=8000,
            api_version_auto_timeout_ms=8000,
        )
        STATS["connected"] = True
        return _producer
    except Exception as exc:
        print(f"[Kafka] producer unavailable: {exc}")
        STATS["connected"] = False
        return None


def publish(topic: str, payload: Dict[str, Any]) -> Optional[str]:
    event = dict(payload)
    event_id = event.get("event_id") or uuid.uuid4().hex
    event["event_id"] = event_id
    event["event_type"] = event.get("event_type") or topic
    event["emitted_at"] = datetime.now(timezone.utc).isoformat()
    producer = _get_producer()
    if producer is None:
        # Still persist to HDFS so the pipeline is not a no-op if Kafka is briefly down
        _persist_to_hdfs(topic, event)
        return event_id
    try:
        producer.send(topic, event)
        producer.flush(timeout=5)
        STATS["produced"] += 1
        STATS["last_event"] = {"topic": topic, "event_id": event_id, "direction": "produced"}
        return event_id
    except Exception as exc:
        print(f"[Kafka] publish failed: {exc}")
        _persist_to_hdfs(topic, event)
        return event_id


def _persist_to_hdfs(topic: str, payload: Dict[str, Any]) -> None:
    line = json.dumps(payload, default=str)
    hdfs_store.append_line("/travelglobe/events/stream.jsonl", line)
    place = str(payload.get("place_name") or payload.get("destination") or "")
    if topic == "travel.analysis" and payload.get("analysis") and place:
        hdfs_store.store_analysis(place, payload["analysis"])
    if topic in ("sar.alerts", "sar.assessed") and place:
        hdfs_store.store_sar(place, payload)
    if topic == "travel.chat":
        hdfs_store.append_line("/travelglobe/chat/turns.jsonl", line)
    origin = str(payload.get("origin") or "").replace(" ", "")
    dest = str(payload.get("place_name") or "").replace(" ", "")
    if origin and dest and topic in ("travel.search", "travel.analysis"):
        hdfs_store.append_line("/travelglobe/graph/edges.tsv", f"{origin} {dest}")


def _ensure_topics() -> None:
    try:
        from kafka.admin import KafkaAdminClient, NewTopic

        admin = KafkaAdminClient(bootstrap_servers=_bootstrap(), client_id="travelglobe-admin")
        existing = set(admin.list_topics())
        missing = [NewTopic(name=t, num_partitions=1, replication_factor=1) for t in TOPICS if t not in existing]
        if missing:
            admin.create_topics(new_topics=missing, validate_only=False)
        admin.close()
        STATS["connected"] = True
        print("[Kafka] topics ready:", TOPICS)
    except Exception as exc:
        print(f"[Kafka] topic setup: {exc}")


def _consume_loop() -> None:
    while True:
        try:
            from kafka import KafkaConsumer

            consumer = KafkaConsumer(
                *TOPICS,
                bootstrap_servers=_bootstrap(),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="travelglobe-hdfs-sink",
                value_deserializer=lambda v: v.decode("utf-8", errors="replace"),
            )
            STATS["connected"] = True
            print("[Kafka] consumer subscribed; sinking events to HDFS")
            for msg in consumer:
                try:
                    payload = json.loads(msg.value)
                except Exception:
                    payload = {"raw": msg.value}
                _persist_to_hdfs(msg.topic, payload)
                STATS["consumed"] += 1
                STATS["last_event"] = {
                    "topic": msg.topic,
                    "offset": msg.offset,
                    "direction": "consumed",
                }
        except Exception as exc:
            STATS["connected"] = False
            print(f"[Kafka] consumer error: {exc}")
            time.sleep(8)


def start_background() -> None:
    def boot():
        for _ in range(15):
            _ensure_topics()
            if STATS["connected"]:
                break
            time.sleep(4)
        _consume_loop()

    threading.Thread(target=boot, daemon=True, name="kafka-hdfs-sink").start()


def kafka_reachable() -> bool:
    try:
        from kafka.admin import KafkaAdminClient

        admin = KafkaAdminClient(bootstrap_servers=_bootstrap(), client_id="health", request_timeout_ms=4000)
        admin.list_topics()
        admin.close()
        return True
    except Exception:
        return False
