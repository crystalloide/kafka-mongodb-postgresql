FROM confluentinc/cp-kafka-connect:7.8.1

ARG JDBC_CONNECTOR_VERSION=10.8.0

RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:${JDBC_CONNECTOR_VERSION}
