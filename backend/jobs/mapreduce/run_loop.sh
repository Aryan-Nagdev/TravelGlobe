#!/bin/bash
echo "[mapreduce] Waiting for HDFS..."
for i in $(seq 1 90); do
  if hdfs dfs -test -e /travelglobe/events; then
    echo "[mapreduce] Input path exists"
    break
  fi
  sleep 5
done

STREAMING_JAR=$(ls ${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -n 1)
echo "[mapreduce] Using $STREAMING_JAR"

while true; do
  echo "[mapreduce] Running Hadoop Streaming MapReduce on /travelglobe/events"
  hdfs dfs -rm -r -f /travelglobe/analytics/popularity || true
  hadoop jar "$STREAMING_JAR" \
    -D mapreduce.framework.name=local \
    -D mapreduce.job.name=travelglobe-destination-popularity \
    -files /jobs/mapper.py,/jobs/reducer.py \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -input /travelglobe/events \
    -output /travelglobe/analytics/popularity \
    && echo "[mapreduce] Job succeeded" \
    || echo "[mapreduce] Job failed (will retry)"
  sleep 45
done
