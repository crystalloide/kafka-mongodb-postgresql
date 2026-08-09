
#####  Installation

1°) Lancer Ubuntu sur la machine windows (Ubuntu 24.4.1 dans cet exemple) 
```bash
ubuntu
```

2°) Prendre le user souhaité :
```bash
su - user
```

3°) Regarder où nous sommes :
```bash
pwd
```

```bash
cd ~
sudo rm -Rf ~/kafka-mongodb-postgresql
git clone https://github.com/crystalloide/kafka-mongodb-postgresql.git 
```

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

### Environnement de formation Python — Kafka / PostgreSQL / MongoDB

### Arborescence :

```
formation-env/
├── docker-compose.yml         
├── kafka/
│   └── Dockerfile            
├── connect/
│   └── Dockerfile
├── hawtio/
│   └── Dockerfile             
├── connect-configs/
│   └── connect-source-postgres.json
│   └── connect-sink-postgres.json
└── postgres/
    └── init.sql                
```

Le build a besoin d'un accès Internet pour télécharger les images Confluent, l'agent Jolokia et le connecteur JDBC via **confluent-hub**

### Choix techniques

- **Kafka 3.8.1** : les images officielles Apache ne publient pas
  directement un tag `3.8.1` stable avec toutes les variables d'env
  pratiques ; j'utilise donc `confluentinc/cp-kafka:7.8.1`, qui embarque
  exactement **Apache Kafka 3.8.1**[web:24][web:17]. 3 noeuds combinés
  `broker,controller` en mode KRaft (pas de rôle controller-only séparé),
  avec un `CLUSTER_ID` fixe pour la persistance entre redémarrages.
- **Kafka Connect** : image `confluentinc/cp-kafka-connect:7.8.1` +
  connecteur **JDBC (source et sink)** installé via `confluent-hub`, qui
  fonctionne nativement avec PostgreSQL sans driver additionnel[web:19].
  Deux exemples de configuration sont fournis (`connect-source-postgres.json`,
  `connect-sink-postgres.json`) à poster sur `http://localhost:8083/connectors`.
- **PostgreSQL 16** avec un script d'init créant une table `clients`
  (source) et une table `clients_sink` (cible du connecteur sink).
- **MongoDB 7.0.7** en single-node standalone (pas de replica set,
  conforme à votre demande d'un seul noeud).
- **Kafka UI** (`provectuslabs/kafka-ui`) : vue cluster, topics, Connect,
  et métriques JMX (port 9999 des brokers).
- **Console JMX** : le choix le plus robuste en environnement Docker est
  **Hawtio + agent Jolokia** embarqué dans chaque broker Kafka (port
  8778). Alternative : `jconsole`/VisualVM depuis l'hôte sur les ports
  9101/9102/9103 (JMX RMI classique).
- **Console Redpanda** (`redpandadata/console`) : totalement compatible
  protocole Kafka, elle fonctionne sans problème contre un cluster Kafka
  standard[web:8][web:15], pointée ici sur les 3 brokers et sur Connect.

### Accès aux interfaces

| Service            | URL                          |
|---------------------|-------------------------------|
| Kafka (client)       | `localhost:9092/9094/9096`   |
| Kafka Connect REST   | `http://localhost:8083`      |
| PostgreSQL           | `localhost:5432` (formation/formation) |
| MongoDB              | `localhost:27017` (formation/formation) |
| Kafka UI             | `http://localhost:8080`      |
| Hawtio (JMX)         | `http://localhost:8888/hawtio`      |
| Console Redpanda     | `http://localhost:8090`      |

### Démarrage

```bash
docker compose build
docker compose up -d
```

```bash
docker compose ps
```

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-source-postgres.json http://localhost:8083/connectors
```

Après l'exécution, vérifiez que le connecteur est bien actif :
```bash
curl http://localhost:8083/connectors
curl http://localhost:8083/connectors/postgres-source-clients/status
```

Affichage en retour : 

```text
["postgres-source-clients","postgres-sink-clients"]{"name":"postgres-source-clients","connector":{"state":"RUNNING","worker_id":"kafka-connect:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"kafka-connect:8083"}],"type":"source"}
```

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-sink-postgres.json http://localhost:8083/connectors
```

### Test de bout en bout :

Pour valider que le pipeline fonctionne réellement (Postgres → Kafka → Postgres), vous pouvez :

#### Consommer les messages produits par le connecteur source

```bash
docker exec -it kafka1 kafka-console-consumer --bootstrap-server localhost:19092 --topic pg-clients --from-beginning --max-messages 3
```

#### Vérifier que le connecteur sink a bien réinjecté les données dans la table clients_sink

```bash
docker exec -it postgres psql -U formation -d formation -c "SELECT * FROM clients_sink;"
Si les 3 clients (Alice, Bruno, Chloé) apparaissent dans clients_sink, le pipeline JDBC source→sink fonctionne de bout en bout.
```

#### Pour supprimer et recréer un connecteur si besoin (par exemple après une modification de config) :

```bash
curl -X DELETE http://localhost:8083/connectors/postgres-sink-clients
```



### Dans Hawtio, cliquer sur **Connect** puis ajouter une connexion distante vers `kafka1:8778`, `kafka2:8778`, `kafka3:8778` (chemin `/jolokia`) pour visualiser les MBeans JMX de chaque broker.

<img width="732" height="473" alt="Add connection hawtio" src="https://github.com/user-attachments/assets/f5c8cd99-ad81-479f-841d-acf60379982b" />

https://github.com/crystalloide/kafka-mongodb-postgresql/tree/d57047d0c5a83a8f9289761907ad08339abd591e/formation-env

### Points d'attention pour la suite

- Générer un nouveau `CLUSTER_ID` si vous dupliquez cet environnement pour
  plusieurs postes (`kafka-storage random-uuid`).
- Les ports hôtes 8080/8083/8090/8888/9092-9096/9101-9103/5432/27017
  doivent être libres sur la machine Ubuntu 24.04.
- Le sizing par défaut (heap JVM Kafka standard) convient pour un poste
  de formation ; ajustez `KAFKA_HEAP_OPTS` si RAM limitée.
