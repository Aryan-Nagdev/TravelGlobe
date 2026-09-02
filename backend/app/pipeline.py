"""Orchestrates HDFS persistence, Kafka events, and Spark/PageRank enrichment."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app import hdfs_store, kafka_bus
from app.bigdata_analytics import pagerank_for, popularity_for, related_destinations, spark_stats_for
from app.config import settings


def load_cached_analysis(place_name: str) -> Optional[Dict[str, Any]]:
    return hdfs_store.load_analysis(place_name)


def persist_destination_analysis(
    place_name: str,
    origin_city: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    crowd = result.get("crowd") or {}
    disaster = result.get("sar_disaster") or {}
    flood = (disaster.get("flood_risk") or {}).get("score", 0)

    rank = pagerank_for(place_name)
    pop = popularity_for(place_name)
    spark_row = spark_stats_for(place_name)
    related = related_destinations(place_name)

    if pop:
        crowd["mapreduce_search_count"] = pop.get("search_count")
        crowd["hadoop_engine"] = "hadoop-mapreduce"
        result["crowd"] = crowd

    recs = result.get("recommendations") or {}
    recs["pagerank_related"] = related
    result["recommendations"] = recs
    result["related_destinations"] = related

    result["bigdata"] = {
        "storage": "hadoop-hdfs",
        "events": "apache-kafka",
        "popularity_job": "hadoop-mapreduce",
        "analytics_job": "apache-spark",
        "ranking": "spark-pagerank",
        "pagerank": rank.get("pagerank"),
        "mapreduce_search_count": pop.get("search_count"),
        "spark_event_count": spark_row.get("event_count"),
        "persisted_at": time.time(),
    }

    hdfs_store.store_analysis(place_name, result)
    if disaster:
        hdfs_store.store_sar(place_name, disaster)

    kafka_bus.publish("travel.search", {
        "place_name": place_name,
        "origin": origin_city,
        "crowd_score": crowd.get("score", 0),
        "flood_score": flood,
    })
    kafka_bus.publish("travel.analysis", {
        "place_name": place_name,
        "origin": origin_city,
        "crowd_score": crowd.get("score", 0),
        "flood_score": flood,
        "analysis": result,
    })
    kafka_bus.publish("sar.assessed", {
        "place_name": place_name,
        "flood_score": flood,
        "landslide_score": (disaster.get("landslide_risk") or {}).get("score", 0),
        "alerts": disaster.get("active_disaster_alerts") or [],
    })
    return result


def persist_chat(message: str, response: Dict[str, Any], place_name: str = "") -> None:
    kafka_bus.publish("travel.chat", {
        "place_name": place_name,
        "message": message,
        "model": response.get("model"),
        "is_groq_llm": response.get("is_groq_llm"),
    })


def cluster_status() -> Dict[str, Any]:
    import httpx

    spark_ok = False
    try:
        spark_ok = httpx.get(settings.SPARK_UI, timeout=3.0).status_code == 200
    except Exception:
        pass
    hdfs_ok = hdfs_store.namenode_reachable()
    kafka_ok = kafka_bus.kafka_reachable()
    mr_files = hdfs_store.list_status("/travelglobe/analytics/popularity")
    pr_files = hdfs_store.list_status("/travelglobe/analytics/pagerank")
    spark_files = hdfs_store.list_status("/travelglobe/analytics/spark")
    return {
        "hdfs": {"status": "connected" if hdfs_ok else "offline", "webhdfs": settings.HDFS_WEBHDFS},
        "kafka": {
            "status": "connected" if kafka_ok else "offline",
            "bootstrap": settings.KAFKA_BOOTSTRAP,
            "stats": kafka_bus.STATS,
            "topics": kafka_bus.TOPICS,
        },
        "mapreduce": {"status": "has-output" if mr_files else "waiting", "files": len(mr_files)},
        "spark": {"status": "connected" if spark_ok else "offline", "ui": settings.SPARK_UI, "files": len(spark_files)},
        "pagerank": {"status": "has-output" if pr_files else "waiting", "files": len(pr_files)},
    }
