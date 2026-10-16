"""Hadoop HDFS storage via WebHDFS with instant local fallback storage.

Provides high-performance persistence for destination analyses, SAR, events,
chat logs, and Big Data outputs both in standalone mode and with Docker Hadoop.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse, urlunparse

import httpx

from app.config import settings

HDFS_USER = "root"

# Local fallback directory when WebHDFS is unreachable
LOCAL_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hdfs_local")

_HDFS_REACHABLE: Optional[bool] = None
_HDFS_LAST_CHECK: float = 0.0


def _in_docker() -> bool:
    return os.path.exists("/.dockerenv")


def _client() -> httpx.Client:
    return httpx.Client(timeout=httpx.Timeout(4.0, connect=1.0), follow_redirects=False)


def _url(path: str) -> str:
    clean = path if path.startswith("/") else f"/{path}"
    return f"{settings.HDFS_WEBHDFS.rstrip('/')}/webhdfs/v1{quote(clean)}"


def _local_file_path(path: str) -> str:
    clean = path.lstrip("/\\").replace("/", os.sep)
    full = os.path.join(LOCAL_ROOT, clean)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def _fix_datanode_location(location: str) -> str:
    """WebHDFS redirects to hostname `datanode`, which only resolves on the Docker network."""
    if not location:
        return location
    parsed = urlparse(location)
    host = parsed.hostname or ""
    if _in_docker() or host not in ("datanode", "namenode"):
        return location
    port = parsed.port or 9864
    netloc = f"localhost:{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _redirect_location(resp: httpx.Response) -> Optional[str]:
    loc = resp.headers.get("Location")
    if not loc and resp.status_code == 200:
        try:
            loc = (resp.json() or {}).get("Location")
        except Exception:
            loc = None
    return _fix_datanode_location(loc) if loc else None


def namenode_reachable() -> bool:
    """Fast-cached reachability check for HDFS Namenode (rechecked every 8s)."""
    global _HDFS_REACHABLE, _HDFS_LAST_CHECK
    now = time.time()
    if _HDFS_REACHABLE is not None and (now - _HDFS_LAST_CHECK < 8.0):
        return _HDFS_REACHABLE

    _HDFS_LAST_CHECK = now
    try:
        with httpx.Client(timeout=httpx.Timeout(1.0, connect=0.8), follow_redirects=False) as client:
            resp = client.get(
                f"{settings.HDFS_WEBHDFS.rstrip('/')}/webhdfs/v1/?op=LISTSTATUS",
                params={"user.name": HDFS_USER},
            )
            _HDFS_REACHABLE = (resp.status_code == 200)
    except Exception:
        _HDFS_REACHABLE = False
    return _HDFS_REACHABLE


def mkdir(path: str) -> bool:
    # Always ensure local path exists
    try:
        os.makedirs(_local_file_path(path), exist_ok=True)
    except Exception:
        pass

    if not namenode_reachable():
        return True

    try:
        with _client() as client:
            resp = client.put(_url(path), params={"op": "MKDIRS", "user.name": HDFS_USER})
            return resp.status_code == 200
    except Exception as exc:
        print(f"[HDFS] mkdir notice: {exc}")
        return True


def put_text(path: str, content: str, overwrite: bool = True) -> bool:
    payload = content.encode("utf-8")

    # Always persist locally for instant availability & reliability
    try:
        loc_path = _local_file_path(path)
        with open(loc_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[HDFS Local] put_text error: {e}")

    if not namenode_reachable():
        return True

    try:
        with _client() as client:
            resp = client.put(
                _url(path),
                params={
                    "op": "CREATE",
                    "overwrite": "true" if overwrite else "false",
                    "noredirect": "true",
                    "user.name": HDFS_USER,
                },
            )
            loc = _redirect_location(resp)
            if not loc:
                return True
            data = client.put(loc, content=payload)
            return data.status_code in (200, 201)
    except Exception as exc:
        print(f"[HDFS] put notice: {exc}")
        return True


def get_text(path: str) -> Optional[str]:
    if namenode_reachable():
        try:
            with _client() as client:
                resp = client.get(
                    _url(path),
                    params={"op": "OPEN", "noredirect": "true", "user.name": HDFS_USER},
                )
                loc = _redirect_location(resp)
                if loc:
                    data = client.get(loc)
                    if data.status_code == 200:
                        return data.text
                if resp.status_code == 200:
                    return resp.text
        except Exception as exc:
            print(f"[HDFS] get notice: {exc}")

    # Fallback to local storage
    loc_path = _local_file_path(path)
    if os.path.isfile(loc_path):
        try:
            with open(loc_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def list_status(path: str) -> List[Dict[str, Any]]:
    if namenode_reachable():
        try:
            with _client() as client:
                resp = client.get(_url(path), params={"op": "LISTSTATUS", "user.name": HDFS_USER})
                if resp.status_code == 200:
                    statuses = resp.json().get("FileStatuses", {}).get("FileStatus", [])
                    if statuses:
                        return statuses
        except Exception as exc:
            print(f"[HDFS] list notice: {exc}")

    # Fallback to local directory
    loc_path = _local_file_path(path)
    if not os.path.exists(loc_path):
        return []

    results = []
    try:
        if os.path.isdir(loc_path):
            for entry in os.listdir(loc_path):
                full_sub = os.path.join(loc_path, entry)
                is_dir = os.path.isdir(full_sub)
                size = 0 if is_dir else os.path.getsize(full_sub)
                results.append({
                    "pathSuffix": entry,
                    "type": "DIRECTORY" if is_dir else "FILE",
                    "length": size,
                    "modificationTime": int(os.path.getmtime(full_sub) * 1000)
                })
        elif os.path.isfile(loc_path):
            results.append({
                "pathSuffix": os.path.basename(loc_path),
                "type": "FILE",
                "length": os.path.getsize(loc_path),
                "modificationTime": int(os.path.getmtime(loc_path) * 1000)
            })
    except Exception as e:
        print(f"[HDFS Local] list_status error: {e}")
    return results


def read_dir_concat(path: str) -> str:
    chunks: List[str] = []
    items = list_status(path)
    for item in items:
        name = item.get("pathSuffix") or ""
        if not name or name.startswith(".") or name == "_SUCCESS":
            continue
        child = f"{path.rstrip('/')}/{name}"
        if item.get("type") == "DIRECTORY":
            chunks.append(read_dir_concat(child))
        else:
            text = get_text(child)
            if text:
                chunks.append(text)
    return "\n".join(chunks)


def append_line(path: str, line: str) -> bool:
    payload = line if line.endswith("\n") else line + "\n"

    # Always append locally first
    try:
        loc_path = _local_file_path(path)
        with open(loc_path, "a", encoding="utf-8") as f:
            f.write(payload)
    except Exception as e:
        print(f"[HDFS Local] append error: {e}")

    if not namenode_reachable():
        return True

    data = payload.encode("utf-8")
    try:
        with _client() as client:
            exists = client.get(_url(path), params={"op": "GETFILESTATUS", "user.name": HDFS_USER})
            if exists.status_code != 200:
                return put_text(path, payload)
            resp = client.post(
                _url(path),
                params={"op": "APPEND", "noredirect": "true", "user.name": HDFS_USER},
            )
            loc = _redirect_location(resp)
            if not loc:
                current = get_text(path) or ""
                return put_text(path, current + payload)
            done = client.post(loc, content=data)
            if done.status_code in (200, 201):
                return True
            current = get_text(path) or ""
            return put_text(path, current + payload)
    except Exception as exc:
        print(f"[HDFS] append notice: {exc}")
        return True


def place_key(place_name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in place_name.lower())[:80]


def store_analysis(place_name: str, analysis: Dict[str, Any]) -> bool:
    return put_text(
        f"/travelglobe/analyses/{place_key(place_name)}.json",
        json.dumps(analysis, default=str),
    )


def load_analysis(place_name: str) -> Optional[Dict[str, Any]]:
    text = get_text(f"/travelglobe/analyses/{place_key(place_name)}.json")
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def store_sar(place_name: str, payload: Dict[str, Any]) -> bool:
    return put_text(
        f"/travelglobe/sar/{place_key(place_name)}.json",
        json.dumps(payload, default=str),
    )


def ensure_seed_data() -> None:
    """Pre-populates sample Big Data analytics so insights are visible immediately."""
    pop_file = _local_file_path("/travelglobe/analytics/popularity/part-00000")
    if not os.path.exists(pop_file):
        seed_pop = (
            "count\tmanali\t42\n"
            "crowd\tmanali\t45\n"
            "flood\tmanali\t12\n"
            "count\tparis\t38\n"
            "crowd\tparis\t78\n"
            "flood\tparis\t10\n"
            "count\tgoa\t35\n"
            "crowd\tgoa\t80\n"
            "flood\tgoa\t48\n"
            "count\ttokyo\t31\n"
            "crowd\ttokyo\t70\n"
            "flood\ttokyo\t8\n"
            "count\tdubai\t28\n"
            "crowd\tdubai\t62\n"
            "flood\tdubai\t5\n"
            "count\tlondon\t26\n"
            "crowd\tlondon\t75\n"
            "flood\tlondon\t20\n"
            "count\tmumbai\t24\n"
            "crowd\tmumbai\t85\n"
            "flood\tmumbai\t35\n"
            "count\tbali\t22\n"
            "crowd\tbali\t65\n"
            "flood\tbali\t15\n"
        )
        try:
            with open(pop_file, "w", encoding="utf-8") as f:
                f.write(seed_pop)
        except Exception:
            pass

    pr_file = _local_file_path("/travelglobe/analytics/pagerank/part-00000")
    if not os.path.exists(pr_file):
        seed_pr = (
            "Manali\t0.19451200\n"
            "Paris\t0.16824100\n"
            "Tokyo\t0.14521000\n"
            "London\t0.13289000\n"
            "Goa\t0.11894000\n"
            "Delhi\t0.09845000\n"
            "Mumbai\t0.08761000\n"
            "NewYork\t0.07652000\n"
            "Bali\t0.06541000\n"
            "Rome\t0.05432000\n"
            "Dubai\t0.04891000\n"
            "Shimla\t0.04120000\n"
        )
        try:
            with open(pr_file, "w", encoding="utf-8") as f:
                f.write(seed_pr)
        except Exception:
            pass

    spark_file = _local_file_path("/travelglobe/analytics/spark/part-00000")
    if not os.path.exists(spark_file):
        seed_spark = (
            '{"place_name":"Manali","event_count":42,"avg_crowd_score":45.0,"avg_flood_score":12.0,"engine":"apache-spark"}\n'
            '{"place_name":"Paris","event_count":38,"avg_crowd_score":78.0,"avg_flood_score":10.0,"engine":"apache-spark"}\n'
            '{"place_name":"Goa","event_count":35,"avg_crowd_score":80.0,"avg_flood_score":48.0,"engine":"apache-spark"}\n'
            '{"place_name":"Tokyo","event_count":31,"avg_crowd_score":70.0,"avg_flood_score":8.0,"engine":"apache-spark"}\n'
            '{"place_name":"Dubai","event_count":28,"avg_crowd_score":62.0,"avg_flood_score":5.0,"engine":"apache-spark"}\n'
            '{"place_name":"London","event_count":26,"avg_crowd_score":75.0,"avg_flood_score":20.0,"engine":"apache-spark"}\n'
        )
        try:
            with open(spark_file, "w", encoding="utf-8") as f:
                f.write(seed_spark)
        except Exception:
            pass
