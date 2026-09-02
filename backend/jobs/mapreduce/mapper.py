#!/usr/bin/env python
"""Hadoop Streaming mapper: destination popularity and risk signals from HDFS event logs."""
from __future__ import print_function
import sys
import json

for raw in sys.stdin:
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    place = "unknown"
    crowd = 0
    flood = 0
    event_type = "event"
    try:
        ev = json.loads(line)
        place = (ev.get("place_name") or ev.get("destination") or "unknown").strip() or "unknown"
        crowd = int(ev.get("crowd_score") or 0)
        flood = int(ev.get("flood_score") or 0)
        event_type = ev.get("event_type") or "event"
    except Exception:
        parts = line.split("\t")
        if parts:
            place = parts[0].strip() or "unknown"
    place = place.replace(" ", "_")
    print("count\t%s\t1" % place)
    print("crowd\t%s\t%d" % (place, crowd))
    print("flood\t%s\t%d" % (place, flood))
    print("etype\t%s\t1" % event_type)
