"""Hadoop HDFS storage via WebHDFS — destination analyses, SAR, events, and chat logs."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse, urlunparse

import httpx

from app.config import settings

HDFS_USER = "root"


def _in_docker() -> bool:
    return os.path.exists("/.dockerenv")


def _client() -> httpx.Client:
    return httpx.Client(timeout=30.0, follow_redirects=False)


def _url(path: str) -> str:
    clean = path if path.startswith("/") else f"/{path}"
    return f"{settings.HDFS_WEBHDFS.rstrip('/')}/webhdfs/v1{quote(clean)}"


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


def mkdir(path: str) -> bool:
    try:
        with _client() as client:
            resp = client.put(_url(path), params={"op": "MKDIRS", "user.name": HDFS_USER})
            return resp.status_code == 200
    except Exception as exc:
        print(f"[HDFS] mkdir failed: {exc}")
        return False


def put_text(path: str, content: str, overwrite: bool = True) -> bool:
    payload = content.encode("utf-8")
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
                print(f"[HDFS] put {path} no datanode location status={resp.status_code}")
                return False
            data = client.put(loc, content=payload)
            if data.status_code in (200, 201):
                return True
            print(f"[HDFS] put data {path} status={data.status_code} {data.text[:200]}")
            return False
    except Exception as exc:
        print(f"[HDFS] put failed: {exc}")
        return False


def get_text(path: str) -> Optional[str]:
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
            return None
    except Exception as exc:
        print(f"[HDFS] get failed: {exc}")
        return None


def list_status(path: str) -> List[Dict[str, Any]]:
    try:
        with _client() as client:
            resp = client.get(_url(path), params={"op": "LISTSTATUS", "user.name": HDFS_USER})
            if resp.status_code != 200:
                return []
            return resp.json().get("FileStatuses", {}).get("FileStatus", []) or []
    except Exception as exc:
        print(f"[HDFS] list failed: {exc}")
        return []


def read_dir_concat(path: str) -> str:
    chunks: List[str] = []
    for item in list_status(path):
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
        print(f"[HDFS] append failed: {exc}")
        return False


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


def namenode_reachable() -> bool:
    try:
        with _client() as client:
            resp = client.get(
                f"{settings.HDFS_WEBHDFS.rstrip('/')}/webhdfs/v1/?op=LISTSTATUS",
                params={"user.name": HDFS_USER},
            )
            return resp.status_code == 200
    except Exception:
        return False
