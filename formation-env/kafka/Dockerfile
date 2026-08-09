# Image Kafka 3.8.1 (fournie par Confluent Platform 7.8.x) enrichie
# de l'agent Jolokia pour exposer JMX en HTTP/JSON (consommé par Hawtio).
#
# Note : depuis Jolokia 2.x, l'artefact Maven a été renommé
# "jolokia-agent-jvm" (au lieu de "jolokia-jvm"), avec le classifier
# "-javaagent". La vérification d'intégrité utilise "jar tf" (fourni
# par le JDK, déjà présent dans l'image de base) plutôt que "unzip",
# absent de l'image confluentinc/cp-kafka.
FROM confluentinc/cp-kafka:7.8.1

USER root

ARG JOLOKIA_VERSION=2.2.9

RUN mkdir -p /opt/jolokia && \
    curl -fsSL -o /opt/jolokia/jolokia-jvm-agent.jar \
    "https://repo1.maven.org/maven2/org/jolokia/jolokia-agent-jvm/${JOLOKIA_VERSION}/jolokia-agent-jvm-${JOLOKIA_VERSION}-javaagent.jar" && \
    jar tf /opt/jolokia/jolokia-jvm-agent.jar > /dev/null && \
    chown -R appuser:appuser /opt/jolokia

USER appuser
