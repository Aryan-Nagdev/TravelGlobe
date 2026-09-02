# Build on the official Apache Spark 3.5.1 image.
# The vanilla image uses eclipse-temurin:17-jre; JAVA_HOME, SPARK_HOME,
# PYTHONPATH and PATH are set in /opt/entrypoint.sh which is the default
# ENTRYPOINT.  When docker-compose overrides the entrypoint with our shell
# script those env-vars are lost, so we re-declare them here explicitly.
FROM apache/spark:3.5.1

USER root

# ---- environment ----------------------------------------------------------
# SPARK_HOME is already /opt/spark in the base image.
ENV SPARK_HOME=/opt/spark

# eclipse-temurin:17-jre sets JAVA_HOME to /opt/java/openjdk.
# Re-export it so spark-submit can find the JVM even without entrypoint.sh.
ENV JAVA_HOME=/opt/java/openjdk

# PySpark needs Python ≥ 3 on both driver and executor.
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Make sure all Spark and Java binaries are on PATH.
ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${JAVA_HOME}/bin:${PATH}"

# PySpark / py4j imports.
ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip"

# ---- run_loop script -------------------------------------------------------
# The script is also mounted as a volume (/jobs/run_loop.sh) at runtime, but
# we copy it into the image as a fallback and to ensure correct permissions.
COPY run_loop.sh /opt/spark/run_loop.sh
RUN chmod +x /opt/spark/run_loop.sh

ENTRYPOINT ["/bin/bash", "/opt/spark/run_loop.sh"]
