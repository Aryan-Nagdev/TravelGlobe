"""Read Hadoop MapReduce, Spark, and PageRank outputs from HDFS."""
from __future__ import annotations

from typing import Any, Dict, List

from app import hdfs_store


def _norm(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def parse_mapreduce_popularity(text: str) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    crowd: Dict[str, int] = {}
    flood: Dict[str, int] = {}
    for line in text.splitlines():
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        metric, key, value = parts[0], parts[1], parts[-1]
        try:
            n = int(float(value))
        except Exception:
            continue
        if metric == "count":
            counts[key] = n
        elif metric == "crowd":
            crowd[key] = n
        elif metric == "flood":
            flood[key] = n
    rows = []
    for place, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        rows.append({
            "place_name": place.replace("_", " "),
            "search_count": n,
            "crowd_sum": crowd.get(place, 0),
            "flood_sum": flood.get(place, 0),
            "engine": "hadoop-mapreduce",
        })
    return rows


def parse_pagerank(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip().strip("()")
        if not line:
            continue
        if "\t" in line:
            name, score = line.split("\t", 1)
        elif "," in line:
            name, score = line.split(",", 1)
            name = name.strip().strip("'\"")
        else:
            continue
        try:
            rows.append({
                "destination": name.strip(),
                "pagerank": float(score),
                "engine": "spark-pagerank",
            })
        except Exception:
            continue
    rows.sort(key=lambda r: -r["pagerank"])
    return rows


def parse_spark_stats(text: str) -> List[Dict[str, Any]]:
    import json

    rows: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    rows.sort(key=lambda r: -int(r.get("event_count") or 0))
    return rows


def popularity() -> Dict[str, Any]:
    text = hdfs_store.read_dir_concat("/travelglobe/analytics/popularity")
    return {"engine": "hadoop-mapreduce", "results": parse_mapreduce_popularity(text)}


def pagerank() -> Dict[str, Any]:
    text = hdfs_store.read_dir_concat("/travelglobe/analytics/pagerank")
    return {"engine": "spark-pagerank", "results": parse_pagerank(text)}


def spark_stats() -> Dict[str, Any]:
    text = hdfs_store.read_dir_concat("/travelglobe/analytics/spark")
    return {"engine": "apache-spark", "results": parse_spark_stats(text)}


def pagerank_for(place_name: str) -> Dict[str, Any]:
    needle = _norm(place_name)
    if not needle:
        return {}
    for row in pagerank().get("results") or []:
        dest = _norm(str(row.get("destination") or ""))
        if dest == needle or needle in dest or dest in needle:
            return row
    return {}


def popularity_for(place_name: str) -> Dict[str, Any]:
    needle = _norm(place_name)
    if not needle:
        return {}
    for row in popularity().get("results") or []:
        dest = _norm(str(row.get("place_name") or ""))
        if dest == needle or needle in dest or dest in needle:
            return row
    return {}


def related_destinations(place_name: str, limit: int = 6) -> List[Dict[str, Any]]:
    needle = _norm(place_name)
    rows = []
    for row in pagerank().get("results") or []:
        dest = str(row.get("destination") or "")
        if _norm(dest) == needle:
            continue
        pop = popularity_for(dest)
        item = dict(row)
        if pop:
            item["search_count"] = pop.get("search_count")
        rows.append(item)
    return rows[:limit]


def spark_stats_for(place_name: str) -> Dict[str, Any]:
    needle = _norm(place_name)
    if not needle:
        return {}
    for row in spark_stats().get("results") or []:
        dest = _norm(str(row.get("place_name") or ""))
        if dest == needle or needle in dest or dest in needle:
            return row
    return {}
