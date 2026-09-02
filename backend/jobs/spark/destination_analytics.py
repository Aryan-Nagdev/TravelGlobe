"""Apache Spark analytics over TravelGlobe event logs stored in HDFS."""
import json
from pyspark.sql import SparkSession

HDFS = "hdfs://namenode:9000"
EVENTS = HDFS + "/travelglobe/events"
OUT = HDFS + "/travelglobe/analytics/spark"


def parse_event(line):
    line = line.strip()
    if not line:
        return None
    try:
        ev = json.loads(line)
        return (
            str(ev.get("place_name") or ev.get("destination") or "unknown"),
            str(ev.get("event_type") or "event"),
            float(ev.get("crowd_score") or 0),
            float(ev.get("flood_score") or 0),
            1,
        )
    except Exception:
        return None


def main():
    spark = (
        SparkSession.builder.appName("TravelGlobeSparkAnalytics")
        .config("spark.hadoop.fs.defaultFS", HDFS)
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .getOrCreate()
    )
    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    hconf = sc._jsc.hadoopConfiguration()
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(hconf)
    Path = spark._jvm.org.apache.hadoop.fs.Path
    out_path = Path(OUT)
    if fs.exists(out_path):
        fs.delete(out_path, True)

    parsed = sc.textFile(EVENTS).map(parse_event).filter(lambda x: x is not None)
    by_place = parsed.map(lambda r: (r[0], (r[2], r[3], r[4]))).reduceByKey(
        lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2])
    )

    def to_json(item):
        place, (crowd_sum, flood_sum, n) = item
        rec = {
            "place_name": place,
            "event_count": int(n),
            "avg_crowd_score": round(crowd_sum / n, 2) if n else 0,
            "avg_flood_score": round(flood_sum / n, 2) if n else 0,
            "engine": "apache-spark",
        }
        return json.dumps(rec)

    by_place.map(to_json).coalesce(1).saveAsTextFile(OUT)
    print("[spark-analytics] Wrote stats to", OUT)
    spark.stop()


if __name__ == "__main__":
    main()
