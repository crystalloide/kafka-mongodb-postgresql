FROM confluentinc/cp-kafka:7.8.1

USER root

ARG JOLOKIA_VERSION=2.2.9

RUN mkdir -p /opt/jolokia && \
    curl -fsSL -o /opt/jolokia/jolokia-jvm-agent.jar \
    "https://repo1.maven.org/maven2/org/jolokia/jolokia-agent-jvm/${JOLOKIA_VERSION}/jolokia-agent-jvm-${JOLOKIA_VERSION}-javaagent.jar" && \
    jar tf /opt/jolokia/jolokia-jvm-agent.jar > /dev/null && \
    chown -R appuser:appuser /opt/jolokia

USER appuser
