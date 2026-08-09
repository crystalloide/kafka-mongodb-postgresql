FROM eclipse-temurin:17-jre-jammy

ARG HAWTIO_VERSION=2.17.7

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL -o /opt/hawtio-app.jar \
    "https://repo1.maven.org/maven2/io/hawt/hawtio-app/${HAWTIO_VERSION}/hawtio-app-${HAWTIO_VERSION}.jar"

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/opt/hawtio-app.jar", "--port", "8080"]
