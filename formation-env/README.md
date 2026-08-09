# Environnement de formation Python — Kafka / PostgreSQL / MongoDB

## Arborescence (fournie dans ce ZIP)

```
formation-env/
├── docker-compose.yml
├── kafka/
│   └── Dockerfile
├── connect/
│   └── Dockerfile
├── hawtio/
│   └── Dockerfile
├── postgres/
│   └── init.sql
└── connect-configs/
    ├── connect-source-postgres.json
    └── connect-sink-postgres.json
```

## Correctif appliqué (v5)

Le build du `kafka/Dockerfile` échouait avec `unzip: command not
found` : l'image de base `confluentinc/cp-kafka` n'embarque pas
`unzip`. La vérification d'intégrité du jar Jolokia utilise désormais
`jar tf` (fourni par le JDK déjà présent dans l'image), qui produit le
même résultat sans dépendance supplémentaire.

## Historique des correctifs précédents

- v2 : `hawtio/hawtio` n'existe pas sur Docker Hub → remplacé.
- v3 : `znio/hawtio` retiré de Docker Hub (dépôt archivé) → Hawtio
  construit localement depuis le jar officiel `hawtio-app` (Maven
  Central).
- v4 : agent Jolokia corrigé (`jolokia-agent-jvm` 2.2.9 au lieu de
  `jolokia-jvm` 1.7.2, jamais publié correctement).
- v5 (ce ZIP) : remplacement de `unzip` (absent) par `jar tf` pour la
  vérification du jar Jolokia pendant le build.

## Choix techniques

- **Kafka 3.8.1** : image `confluentinc/cp-kafka:7.8.1`, qui embarque
  exactement Apache Kafka 3.8.1. 3 noeuds combinés `broker,controller`
  en mode KRaft, avec un `CLUSTER_ID` fixe pour la persistance entre
  redémarrages.
- **Kafka Connect** : image `confluentinc/cp-kafka-connect:7.8.1` +
  connecteur JDBC (source et sink) installé via `confluent-hub`,
  fonctionnant nativement avec PostgreSQL sans driver additionnel.
- **PostgreSQL 16** avec script d'init créant `clients` (source) et
  `clients_sink` (cible du connecteur sink).
- **MongoDB 7.0.7** en single-node standalone.
- **Kafka UI** (`provectuslabs/kafka-ui`).
- **Console JMX** : Hawtio construit localement + agent Jolokia 2.2.9
  embarqué dans chaque broker.
- **Console Redpanda** (`redpandadata/console`) pointée sur le cluster
  Kafka et sur Connect.

## Accès aux interfaces

| Service            | URL                          |
|---------------------|-------------------------------|
| Kafka (client)       | `localhost:9092/9094/9096`   |
| Kafka Connect REST   | `http://localhost:8083`      |
| PostgreSQL           | `localhost:5432` (formation/formation) |
| MongoDB              | `localhost:27017` (formation/formation) |
| Kafka UI             | `http://localhost:8080`      |
| Hawtio (JMX)         | `http://localhost:8888/hawtio` |
| Console Redpanda     | `http://localhost:8090`      |

## Démarrage

```bash
cd formation-env
docker compose build --no-cache
docker compose up -d
docker compose ps

curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-source-postgres.json http://localhost:8083/connectors
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-sink-postgres.json http://localhost:8083/connectors
```

Dans Hawtio (`http://localhost:8888/hawtio`), cliquer sur **Connect**
puis ajouter une connexion distante vers `kafka1:8778`, `kafka2:8778`,
`kafka3:8778` (chemin `/jolokia`) pour visualiser les MBeans JMX de
chaque broker.

## Points d'attention

- Générer un nouveau `CLUSTER_ID` si vous dupliquez cet environnement
  pour plusieurs postes (`docker run --rm confluentinc/cp-kafka:7.8.1
  kafka-storage random-uuid`).
- Les ports hôtes 8080/8083/8090/8888/9092-9096/9101-9103/5432/27017
  doivent être libres sur la machine Ubuntu 24.04.
- Ajustez `KAFKA_HEAP_OPTS` si la RAM du poste de formation est limitée.
