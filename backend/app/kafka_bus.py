"""Apache Kafka event bus — with non-blocking resilience and HDFS event sinking."""
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
_last_producer_attempt = 0.0
_PRODUCER_COOLDOWN = 15.0 # seconds before retrying when Kafka broker is unreachable

_kafka_reachable_cached: Optional[bool] = None
_kafka_last_check = 0.0


def _bootstrap() -> str:
    return settings.KAFKA_BOOTSTRAP


def _get_producer():
    global _producer, _last_producer_attempt
    if _producer is not None:
        return _producer

    now = time.time()
    if now - _last_producer_attempt < _PRODUCER_COOLDOWN:
        return None

    with _lock:
        if _producer is not None:
            return _producer
        _last_producer_attempt = now
        try:
            from kafka import KafkaProducer

            _producer = KafkaProducer(
                bootstrap_servers=_bootstrap(),
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                retries=1,
                acks=1,
                request_timeout_ms=2000,
                api_version_auto_timeout_ms=2000,
            )
            STATS["connected"] = True
            return _producer
        except Exception as exc:
            print(f"[Kafka] broker offline notice: {exc}")
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
        # Asynchronously or directly persist event to HDFS / local storage
        threading.Thread(target=_persist_to_hdfs, args=(topic, event), daemon=True).start()
        STATS["produced"] += 1
        STATS["last_event"] = {"topic": topic, "event_id": event_id, "direction": "produced"}
        return event_id

    try:
        producer.send(topic, event)
        STATS["produced"] += 1
        STATS["last_event"] = {"topic": topic, "event_id": event_id, "direction": "produced"}
        return event_id
    except Exception as exc:
        print(f"[Kafka] publish error notice: {exc}")
        threading.Thread(target=_persist_to_hdfs, args=(topic, event), daemon=True).start()
        return event_id


def _persist_to_hdfs(topic: str, payload: Dict[str, Any]) -> None:
    try:
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
    except Exception as e:
        print(f"[HDFS Sink] Notice: {e}")


def _ensure_topics() -> None:
    try:
        from kafka.admin import KafkaAdminClient, NewTopic

        admin = KafkaAdminClient(
            bootstrap_servers=_bootstrap(),
            client_id="travelglobe-admin",
            request_timeout_ms=2000,
            api_version_auto_timeout_ms=2000
        )
        existing = set(admin.list_topics())
        missing = [NewTopic(name=t, num_partitions=1, replication_factor=1) for t in TOPICS if t not in existing]
        if missing:
            admin.create_topics(new_topics=missing, validate_only=False)
        admin.close()
        STATS["connected"] = True
        print("[Kafka] topics ready:", TOPICS)
    except Exception as exc:
        print(f"[Kafka] topic setup notice: {exc}")


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
                consumer_timeout_ms=3000,
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
            time.sleep(15)


def start_background() -> None:
    def boot():
        for _ in range(3):
            _ensure_topics()
            if STATS["connected"]:
                break
            time.sleep(3)
        if STATS["connected"]:
            _consume_loop()

    threading.Thread(target=boot, daemon=True, name="kafka-hdfs-sink").start()


def kafka_reachable() -> bool:
    global _kafka_reachable_cached, _kafka_last_check
    now = time.time()
    if _kafka_reachable_cached is not None and (now - _kafka_last_check < 8.0):
        return _kafka_reachable_cached

    _kafka_last_check = now
    try:
        from kafka.admin import KafkaAdminClient

        admin = KafkaAdminClient(
            bootstrap_servers=_bootstrap(),
            client_id="health",
            request_timeout_ms=1000,
            api_version_auto_timeout_ms=1000
        )
        admin.list_topics()
        admin.close()
        _kafka_reachable_cached = True
        return True
    except Exception:
        _kafka_reachable_cached = False
        return False
