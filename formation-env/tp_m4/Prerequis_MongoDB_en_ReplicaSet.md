
#####  Pré-requis

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
rm docker-compose.yml.save
cp docker-compose.yml docker-compose.yml.save
vi docker-compose.yml
```
Contenu du fichier  à mettre :
```texte
x-kafka-common: &kafka-common
  build:
    context: ./kafka
    dockerfile: Dockerfile
  image: formation/kafka-jolokia:7.8.1
  restart: unless-stopped
  networks:
    - formation-net
  environment: &kafka-common-env
    CLUSTER_ID: "vSZzm591SZ2njloM9ETImg"
    KAFKA_PROCESS_ROLES: "broker,controller"
    KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka1:9093,2@kafka2:9093,3@kafka3:9093"
    KAFKA_CONTROLLER_LISTENER_NAMES: "CONTROLLER"
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT"
    KAFKA_INTER_BROKER_LISTENER_NAME: "PLAINTEXT"
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
    KAFKA_DEFAULT_REPLICATION_FACTOR: 3
    KAFKA_MIN_INSYNC_REPLICAS: 2
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    KAFKA_JMX_PORT: 9999
    KAFKA_OPTS: "-javaagent:/opt/jolokia/jolokia-jvm-agent.jar=port=8778,host=0.0.0.0"
    KAFKA_DELETE_TOPIC_ENABLE: "true"

services:

  kafka1:
    <<: *kafka-common
    container_name: kafka1
    hostname: kafka1
    ports:
      - "9092:9092"
      - "9101:9999"
      - "8778:8778"
    environment:
      <<: *kafka-common-env
      KAFKA_NODE_ID: 1
      KAFKA_LISTENERS: "PLAINTEXT://0.0.0.0:19092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9092"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka1:19092,PLAINTEXT_HOST://localhost:9092"
      KAFKA_JMX_HOSTNAME: "kafka1"
    volumes:
      - kafka1-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:19092"]
      interval: 15s
      timeout: 10s
      retries: 15
      start_period: 60s

  kafka2:
    <<: *kafka-common
    container_name: kafka2
    hostname: kafka2
    ports:
      - "9094:9094"
      - "9102:9999"
      - "8779:8778"
    environment:
      <<: *kafka-common-env
      KAFKA_NODE_ID: 2
      KAFKA_LISTENERS: "PLAINTEXT://0.0.0.0:19092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9094"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka2:19092,PLAINTEXT_HOST://localhost:9094"
      KAFKA_JMX_HOSTNAME: "kafka2"
    volumes:
      - kafka2-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:19092"]
      interval: 15s
      timeout: 10s
      retries: 15
      start_period: 60s

  kafka3:
    <<: *kafka-common
    container_name: kafka3
    hostname: kafka3
    ports:
      - "9096:9096"
      - "9103:9999"
      - "8780:8778"
    environment:
      <<: *kafka-common-env
      KAFKA_NODE_ID: 3
      KAFKA_LISTENERS: "PLAINTEXT://0.0.0.0:19092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9096"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka3:19092,PLAINTEXT_HOST://localhost:9096"
      KAFKA_JMX_HOSTNAME: "kafka3"
    volumes:
      - kafka3-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:19092"]
      interval: 15s
      timeout: 10s
      retries: 15
      start_period: 60s

  kafka-connect:
    build:
      context: ./connect
      dockerfile: Dockerfile
    image: formation/kafka-connect-jdbc:7.8.1
    container_name: kafka-connect
    hostname: kafka-connect
    restart: unless-stopped
    depends_on:
      kafka1:
        condition: service_healthy
      kafka2:
        condition: service_healthy
      kafka3:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - formation-net
    ports:
      - "8083:8083"
    environment:
      CONNECT_BOOTSTRAP_SERVERS: "kafka1:19092,kafka2:19092,kafka3:19092"
      CONNECT_REST_ADVERTISED_HOST_NAME: "kafka-connect"
      CONNECT_REST_PORT: 8083
      CONNECT_GROUP_ID: "formation-connect-cluster"
      CONNECT_CONFIG_STORAGE_TOPIC: "_connect-configs"
      CONNECT_OFFSET_STORAGE_TOPIC: "_connect-offsets"
      CONNECT_STATUS_STORAGE_TOPIC: "_connect-status"
      CONNECT_CONFIG_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_OFFSET_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_STATUS_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_KEY_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_VALUE_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_KEY_CONVERTER_SCHEMAS_ENABLE: "false"
      CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE: "false"
      CONNECT_INTERNAL_KEY_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_INTERNAL_VALUE_CONVERTER: "org.apache.kafka.connect.json.JsonConverter"
      CONNECT_PLUGIN_PATH: "/usr/share/java,/usr/share/confluent-hub-components"
      CONNECT_LOG4J_ROOT_LOGLEVEL: "INFO"

  postgres:
    image: postgres:16
    container_name: postgres
    restart: unless-stopped
    networks:
      - formation-net
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: formation
      POSTGRES_PASSWORD: formation
      POSTGRES_DB: formation
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U formation -d formation"]
      interval: 10s
      timeout: 5s
      retries: 10

  mongodb:
    image: mongo:7.0.7
    container_name: mongodb
    restart: unless-stopped
    networks:
      - formation-net
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: formation
      MONGO_INITDB_ROOT_PASSWORD: formation
      MONGO_INITDB_DATABASE: formation
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all", "--keyFile", "/etc/secrets/mongo-keyfile"]
    #command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    volumes:
      - mongo-data:/data/db
      - ./mongo-keyfile:/etc/secrets/mongo-keyfile:ro
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 10

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    restart: unless-stopped
    depends_on:
      - kafka1
      - kafka2
      - kafka3
      - kafka-connect
    networks:
      - formation-net
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: "formation-cluster"
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: "kafka1:19092,kafka2:19092,kafka3:19092"
      KAFKA_CLUSTERS_0_METRICS_PORT: 9999
      KAFKA_CLUSTERS_0_KAFKACONNECT_0_NAME: "connect-postgres"
      KAFKA_CLUSTERS_0_KAFKACONNECT_0_ADDRESS: "http://kafka-connect:8083"

  # -------------------------------------------------------------
  # Console JMX - Hawtio construite localement (jar officiel Maven
  # Central io.hawt:hawtio-app). "hawtio.proxyAllowlist=*" autorise
  # la connexion Jolokia vers des hôtes distants (kafka1/2/3) : par
  # défaut Hawtio ne whitelist que localhost pour des raisons de
  # sécurité.
  # -------------------------------------------------------------
  hawtio:
    build:
      context: ./hawtio
      dockerfile: Dockerfile
    image: formation/hawtio:2.17.7
    container_name: hawtio
    restart: unless-stopped
    depends_on:
      - kafka1
      - kafka2
      - kafka3
    networks:
      - formation-net
    ports:
      - "8888:8080"
    environment:
      JAVA_TOOL_OPTIONS: "-Dhawtio.proxyAllowlist=* -Dhawtio.proxyWhitelist=*"
    # Connect -> Name: kafka1 / Scheme: http / Host: kafka1 / Port: 8778 / Path: /jolokia

  # -------------------------------------------------------------
  # Console Redpanda - la clé racine pour Kafka Connect s'appelle
  # "kafkaConnect" (et non "connect") dans les versions récentes.
  # -------------------------------------------------------------
  redpanda-console:
    image: docker.redpanda.com/redpandadata/console:latest
    container_name: redpanda-console
    restart: unless-stopped
    depends_on:
      - kafka1
      - kafka2
      - kafka3
      - kafka-connect
    networks:
      - formation-net
    ports:
      - "8090:8080"
    environment:
      CONFIG_FILEPATH: /tmp/config.yml
      CONSOLE_CONFIG_FILE: |
        kafka:
          brokers: ["kafka1:19092", "kafka2:19092", "kafka3:19092"]
        kafkaConnect:
          enabled: true
          clusters:
            - name: connect-postgres
              url: http://kafka-connect:8083
    command: -c "echo \"$$CONSOLE_CONFIG_FILE\" > /tmp/config.yml; /app/console"
    entrypoint: /bin/sh

networks:
  formation-net:
    driver: bridge

volumes:
  kafka1-data:
  kafka2-data:
  kafka3-data:
  postgres-data:
  mongo-data:
```

### (Re)-créeation si besoin du keyfile obligatoire pour MongoDB en ReplicaSet : 

```bash
cd ~/kafka-mongodb-postgresql/formation-env
ls -l mongo-keyfile
```

#### Génération du secret
```bash
openssl rand -base64 756 > mongo-keyfile
```

#### Droits et propriétaire (999 = user mongodb dans le conteneur)

```bash
sudo chmod 400 mongo-keyfile   # lecture seule pour le propriétaire, rien pour group/others
sudo chown 999:999 mongo-keyfile
```


### Modification de env avec l'URI correspondant à mongoDB en ReplicaSet : 

Il faut s'assurer de l'URI pour un ReplicaSet : MONGO_URI avec **replicaSet=rs0** :

```text
MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0
```

Modifions donc les informations : 

```bash
vi ~/kafka-mongodb-postgresql/formation-env/.env
```

contenu à mettre :

```text
# Endpoints environnement de formation Kafka / MongoDB / CQRS
# A charger avec python-dotenv (load_dotenv())

# Kafka - cluster KRaft 3 noeuds (controller/broker)
# Port host different par broker (listener PLAINTEXT_HOST) :
# kafka1 -> 9092, kafka2 -> 9094, kafka3 -> 9096
# (9093 est le port interne du listener CONTROLLER, jamais expose a l'hote)
KAFKA_BOOTSTRAP=localhost:9092,localhost:9094,localhost:9096

# MongoDB - noeud unique, utilisateur root cree via MONGO_INITDB_ROOT_USERNAME/PASSWORD
#MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin
MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0

# Consoles de supervision / UI
KAFKA_UI=http://localhost:8080
HAWTIO=http://localhost:8888/hawtio
REDPANDA_CONSOLE=http://localhost:8090

# Kafka Connect (REST API) - utile pour tester via Thunder Client
KAFKA_CONNECT=http://localhost:8083
```

```bash
vi ~/kafka-mongodb-postgresql/formation-env/tp_m4/.env
```

mettre le même contenu que précédemment 


### Relance de la pile avec mongo en ReplicaSet : 

```bash
cd ~/kafka-mongodb-postgresql/formation-env
docker compose down
docker compose up -d
```

### Vérification de l'état du conteneur mongodb et de la log : 
```bash
docker ps
docker logs mongodb | tail -n 20
```
**Important** : 
Si l'erreur suivante apparait "errmsg":"permissions on /etc/secrets/mongo-keyfile are too open" apparaît, il faut corriger les droits du fichier **mongo-keyfile**


### Initialisation du ReplicaSet  :

```bash
docker exec -it mongodb mongosh \
  -u formation -p formation --authenticationDatabase admin \
  --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"localhost:27017"}]})'
```

### Vérification de l'état du ReplicaSet  :

```bash
docker exec -it mongodb mongosh \
  -u formation -p formation --authenticationDatabase admin \
  --eval 'rs.status()'
```

On doit voir **set: "rs0"** et un membre **PRIMARY**

exemple : 

```Exemple
{
  set: 'rs0',
  date: ISODate('2026-08-25T21:10:47.449Z'),
  myState: 1,
  term: Long('1'),
  syncSourceHost: '',
  syncSourceId: -1,
  heartbeatIntervalMillis: Long('2000'),
  majorityVoteCount: 1,
  writeMajorityCount: 1,
  votingMembersCount: 1,
  writableVotingMembersCount: 1,
  optimes: {
    lastCommittedOpTime: { ts: Timestamp({ t: 1787692243, i: 23 }), t: Long('1') },
    lastCommittedWallTime: ISODate('2026-08-25T21:10:43.833Z'),
    readConcernMajorityOpTime: { ts: Timestamp({ t: 1787692243, i: 23 }), t: Long('1') },
    appliedOpTime: { ts: Timestamp({ t: 1787692243, i: 23 }), t: Long('1') },
    durableOpTime: { ts: Timestamp({ t: 1787692243, i: 23 }), t: Long('1') },
    lastAppliedWallTime: ISODate('2026-08-25T21:10:43.833Z'),
    lastDurableWallTime: ISODate('2026-08-25T21:10:43.833Z')
  },
  lastStableRecoveryTimestamp: Timestamp({ t: 1787692243, i: 1 }),
  electionCandidateMetrics: {
    lastElectionReason: 'electionTimeout',
    lastElectionDate: ISODate('2026-08-25T21:10:43.445Z'),
    electionTerm: Long('1'),
    lastCommittedOpTimeAtElection: { ts: Timestamp({ t: 1787692243, i: 1 }), t: Long('-1') },
    lastSeenOpTimeAtElection: { ts: Timestamp({ t: 1787692243, i: 1 }), t: Long('-1') },
    numVotesNeeded: 1,
    priorityAtElection: 1,
    electionTimeoutMillis: Long('10000'),
    newTermStartDate: ISODate('2026-08-25T21:10:43.523Z'),
    wMajorityWriteAvailabilityDate: ISODate('2026-08-25T21:10:43.569Z')
  },
  members: [
    {
      _id: 0,
      name: 'localhost:27017',
      health: 1,
      state: 1,
      stateStr: 'PRIMARY',
      uptime: 45,
      optime: { ts: Timestamp({ t: 1787692243, i: 23 }), t: Long('1') },
      optimeDate: ISODate('2026-08-25T21:10:43.000Z'),
      lastAppliedWallTime: ISODate('2026-08-25T21:10:43.833Z'),
      lastDurableWallTime: ISODate('2026-08-25T21:10:43.833Z'),
      syncSourceHost: '',
      syncSourceId: -1,
      infoMessage: 'Could not find member to sync from',
      electionTime: Timestamp({ t: 1787692243, i: 2 }),
      electionDate: ISODate('2026-08-25T21:10:43.000Z'),
      configVersion: 1,
      configTerm: 1,
      self: true,
      lastHeartbeatMessage: ''
    }
  ],
  ok: 1,
  '$clusterTime': {
    clusterTime: Timestamp({ t: 1787692243, i: 23 }),
    signature: {
      hash: Binary.createFromBase64('QEdfIIpjp5SUwQ0h8Wpv2J+TWSk=', 0),
      keyId: Long('7678079718997884934')
    }
  },
  operationTime: Timestamp({ t: 1787692243, i: 23 })
}
```

Reprenons le déroulé des TPs maintenant :-)

