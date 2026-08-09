# Fichier: kafka/Dockerfile
# Image Kafka 3.8.1 (fournie par Confluent Platform 7.8.x) enrichie
# de l'agent Jolokia pour exposer JMX en HTTP/JSON (consommé par Hawtio).
FROM confluentinc/cp-kafka:7.8.1

USER root

ARG JOLOKIA_VERSION=1.7.2

RUN mkdir -p /opt/jolokia && \
    curl -fsSL -o /opt/jolokia/jolokia-jvm-agent.jar \
    "https://repo1.maven.org/maven2/org/jolokia/jolokia-jvm/${JOLOKIA_VERSION}/jolokia-jvm-${JOLOKIA_VERSION}-agent.jar" && \
    chown -R appuser:appuser /opt/jolokia || true

USER appuser
