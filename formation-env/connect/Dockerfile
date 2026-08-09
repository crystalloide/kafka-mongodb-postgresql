# Fichier: connect/Dockerfile
# Kafka Connect 7.8.1 (Kafka 3.8.1) + connecteur JDBC Confluent
# (source ET sink) pour PostgreSQL. Le driver PostgreSQL JDBC 4.0
# est déjà embarqué dans le connecteur, aucune étape supplémentaire
# n'est nécessaire pour PostgreSQL.
FROM confluentinc/cp-kafka-connect:7.8.1

ARG JDBC_CONNECTOR_VERSION=10.8.0

RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:${JDBC_CONNECTOR_VERSION}
