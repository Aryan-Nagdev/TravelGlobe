#!/bin/bash
# ---------------------------------------------------------------------------
# Spark-jobs run loop
# Submits PageRank and destination-analytics jobs against the TravelGlobe
# Spark standalone cluster, retrying indefinitely every 60 seconds.
# ---------------------------------------------------------------------------

# Do NOT use set -e globally – the readiness loop must tolerate command
# failures without killing the whole script.  Individual critical failures
# are handled explicitly below.

# Ensure JAVA_HOME is found even if the build ENV was somehow missing.
# eclipse-temurin:17-jre stores it at /opt/java/openjdk; fall back to
# dynamic detection (same logic as /opt/entrypoint.sh).
if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME="$(java -XshowSettings:properties -version 2>&1 >/dev/null \
               | grep 'java.home' | awk '{print $3}')" || true
  export JAVA_HOME
fi

export SPARK_HOME="${SPARK_HOME:-/opt/spark}"
export PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${JAVA_HOME}/bin:${PATH}"
export PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip"
export PYSPARK_PYTHON="${PYSPARK_PYTHON:-python3}"
export PYSPARK_DRIVER_PYTHON="${PYSPARK_DRIVER_PYTHON:-python3}"

# ---------------------------------------------------------------------------
# Readiness: wait for HDFS NameNode WebHDFS.
# ---------------------------------------------------------------------------
echo "[spark-jobs] Waiting for HDFS NameNode (up to 360 s)..."

HDFS_URL="http://namenode:9870/webhdfs/v1/?op=LISTSTATUS"
HDFS_READY=false

for i in $(seq 1 90); do
  if python3 -c "
import urllib.request, sys
try:
    urllib.request.urlopen('${HDFS_URL}', timeout=3)
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
    echo "[spark-jobs] HDFS NameNode is ready (attempt ${i})"
    HDFS_READY=true
    break
  elif curl -sf --max-time 3 "${HDFS_URL}" >/dev/null 2>&1; then
    echo "[spark-jobs] HDFS NameNode is ready via curl (attempt ${i})"
    HDFS_READY=true
    break
  else
    echo "[spark-jobs] Attempt ${i}/90 – NameNode not ready, waiting 4 s..."
    sleep 4
  fi
done

if [ "${HDFS_READY}" != "true" ]; then
  echo "[spark-jobs] ERROR: NameNode did not become ready within 360 s. Exiting."
  exit 1
fi

# Extra grace period for Spark master to register its workers.
echo "[spark-jobs] Giving Spark master 8 s extra grace..."
sleep 8

# ---------------------------------------------------------------------------
# Main loop: submit jobs forever.
# ---------------------------------------------------------------------------
SUBMIT="${SPARK_HOME}/bin/spark-submit"
MASTER="spark://spark-master:7077"
COMMON_CONFS=(
  "--conf" "spark.hadoop.fs.defaultFS=hdfs://namenode:9000"
  "--conf" "spark.hadoop.dfs.client.use.datanode.hostname=true"
  "--conf" "spark.hadoop.dfs.replication=1"
)

# Python files are at /jobs (volume mount). The Dockerfile also bakes the
# run_loop.sh into /opt/spark/run_loop.sh for startup, but the Python job
# scripts are only available via the volume mount.
JOBS_DIR="/jobs"

while true; do
  echo "[spark-jobs] ── Submitting PageRank ──"
  "${SUBMIT}" \
    --master "${MASTER}" \
    "${COMMON_CONFS[@]}" \
    "${JOBS_DIR}/pagerank.py" \
    || echo "[spark-jobs] PageRank failed (will retry in next cycle)"

  echo "[spark-jobs] ── Submitting destination analytics ──"
  "${SUBMIT}" \
    --master "${MASTER}" \
    "${COMMON_CONFS[@]}" \
    "${JOBS_DIR}/destination_analytics.py" \
    || echo "[spark-jobs] Destination analytics failed (will retry in next cycle)"

  echo "[spark-jobs] Cycle complete – sleeping 60 s..."
  sleep 60
done
