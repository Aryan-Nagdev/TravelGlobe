FROM bde2020/hadoop-base:2.0.0-hadoop3.2.1-java8

RUN set -eux; \
  if [ -f /etc/apt/sources.list ]; then \
    sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list; \
    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list; \
    sed -i '/stretch-updates/d' /etc/apt/sources.list; \
  fi; \
  apt-get update; \
  apt-get install -y --no-install-recommends python3; \
  ln -sf /usr/bin/python3 /usr/bin/python; \
  rm -rf /var/lib/apt/lists/*

COPY mapper.py /jobs/mapper.py
COPY reducer.py /jobs/reducer.py
COPY run_loop.sh /jobs/run_loop.sh
RUN chmod +x /jobs/mapper.py /jobs/reducer.py /jobs/run_loop.sh

WORKDIR /jobs
CMD ["/jobs/run_loop.sh"]
