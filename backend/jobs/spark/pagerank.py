"""Apache Spark PageRank over the TravelGlobe destination graph in HDFS."""
from pyspark.sql import SparkSession

HDFS = "hdfs://namenode:9000"
EDGES = HDFS + "/travelglobe/graph/edges.tsv"
OUT = HDFS + "/travelglobe/analytics/pagerank"
ITERATIONS = 15
DAMPING = 0.85


def main():
    spark = (
        SparkSession.builder.appName("TravelGlobePageRank")
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

    lines = sc.textFile(EDGES)
    links = (
        lines.filter(lambda l: l.strip() and not l.startswith("#"))
        .map(lambda l: l.split())
        .filter(lambda p: len(p) >= 2)
        .map(lambda p: (p[0], p[1]))
        .distinct()
        .groupByKey()
        .mapValues(list)
        .cache()
    )

    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))
    dest_nodes = (
        lines.filter(lambda l: l.strip() and not l.startswith("#"))
        .map(lambda l: l.split())
        .filter(lambda p: len(p) >= 2)
        .map(lambda p: (p[1], 1.0))
        .distinct()
    )
    ranks = ranks.union(dest_nodes).reduceByKey(lambda a, b: a)

    for _ in range(ITERATIONS):
        contribs = links.join(ranks).flatMap(
            lambda url_n_r: [
                (dest, url_n_r[1][1] / max(len(url_n_r[1][0]), 1))
                for dest in url_n_r[1][0]
            ]
        )
        ranks = contribs.reduceByKey(lambda x, y: x + y).mapValues(
            lambda rank: (1.0 - DAMPING) + DAMPING * rank
        )

    formatted = ranks.map(lambda kv: "%s\t%.8f" % (kv[0], kv[1])).sortBy(
        lambda row: -float(row.split("\t")[1])
    )
    formatted.coalesce(1).saveAsTextFile(OUT)
    print("[spark-pagerank] Wrote ranks to", OUT)
    spark.stop()


if __name__ == "__main__":
    main()
