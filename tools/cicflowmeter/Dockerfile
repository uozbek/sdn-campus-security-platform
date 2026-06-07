FROM gradle:4.2-jdk8

USER root

RUN apt-get update && apt-get install -y \
    git \
    libpcap-dev \
    tcpdump \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone https://github.com/ahlashkari/CICFlowMeter.git

WORKDIR /opt/CICFlowMeter

RUN chmod +x gradlew 2>/dev/null || true

RUN ./gradlew clean build -x test || true

WORKDIR /data

COPY run_cicflowmeter.sh /usr/local/bin/run_cicflowmeter.sh
RUN chmod +x /usr/local/bin/run_cicflowmeter.sh

ENTRYPOINT ["/usr/local/bin/run_cicflowmeter.sh"]