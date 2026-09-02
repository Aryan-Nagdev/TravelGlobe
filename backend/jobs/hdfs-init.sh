#!/bin/bash
# ---------------------------------------------------------------------------
# HDFS initialisation – runs once as an init container.
# Creates required directories and seeds graph/event data from /seed/.
# ---------------------------------------------------------------------------
# NOTE: we deliberately do NOT use set -e at the top level because the
# readiness loop must tolerate hdfs command failures without aborting.

echo "[hdfs-init] Waiting for NameNode to become ready (up to 360 s)..."

ready=false
for i in $(seq 1 90); do
  # Suppress errors here; the NameNode may not be ready yet.
  if hdfs dfs -ls / >/dev/null 2>&1; then
    echo "[hdfs-init] NameNode is ready (attempt ${i})"
    ready=true
    break
  fi
  echo "[hdfs-init] Attempt ${i}/90 – not ready, waiting 4 s..."
  sleep 4
done

if [ "${ready}" != "true" ]; then
  echo "[hdfs-init] ERROR: NameNode did not become ready in time. Exiting."
  exit 1
fi

# From here onwards we want hard errors so any HDFS command failure is visible.
set -e

hdfs dfs -mkdir -p \
  /travelglobe/events \
  /travelglobe/analyses \
  /travelglobe/sar \
  /travelglobe/chat \
  /travelglobe/graph \
  /travelglobe/analytics

hdfs dfs -put -f /seed/edges.tsv         /travelglobe/graph/edges.tsv
hdfs dfs -put -f /seed/sample_events.jsonl /travelglobe/events/sample_events.jsonl

# Relax permissions so Spark / MapReduce containers can read/write.
hdfs dfs -chmod -R 777 /travelglobe || true

echo "[hdfs-init] HDFS seed loaded successfully."
hdfs dfs -ls -R /travelglobe
