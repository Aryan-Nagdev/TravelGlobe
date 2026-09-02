#!/usr/bin/env python
"""Hadoop Streaming reducer: aggregate MapReduce keys written to HDFS."""
from __future__ import print_function
import sys

current_key = None
total = 0

for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) < 3:
        continue
    key = parts[0] + "\t" + parts[1]
    try:
        value = int(float(parts[2]))
    except Exception:
        value = 0
    if current_key == key:
        total += value
    else:
        if current_key is not None:
            print("%s\t%d" % (current_key, total))
        current_key = key
        total = value

if current_key is not None:
    print("%s\t%d" % (current_key, total))
