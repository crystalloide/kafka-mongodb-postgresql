# Console JMX web "Hawtio", construite depuis le jar exécutable
# officiel publié sur Maven Central (io.hawt:hawtio-app).
# Alternative robuste : les anciennes images tierces "hawtio/hawtio"
# et "znio/hawtio" ont été retirées de Docker Hub (dépôts archivés).
FROM eclipse-temurin:17-jre-jammy

ARG HAWTIO_VERSION=2.17.7

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL -o /opt/hawtio-app.jar \
    "https://repo1.maven.org/maven2/io/hawt/hawtio-app/${HAWTIO_VERSION}/hawtio-app-${HAWTIO_VERSION}.jar"

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/opt/hawtio-app.jar", "--port", "8080"]
