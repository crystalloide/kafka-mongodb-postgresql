
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
  exactement **Apache Kafka 3.8.1**. 3 noeuds combinés
  `broker,controller` en mode KRaft (pas de rôle controller-only séparé),
  avec un `CLUSTER_ID` fixe pour la persistance entre redémarrages.
- **Kafka Connect** : image `confluentinc/cp-kafka-connect:7.8.1` +
  connecteur **JDBC (source et sink)** installé via `confluent-hub`, qui
  fonctionne nativement avec PostgreSQL sans driver additionnel.
  Deux exemples de configuration sont fournis (`connect-source-postgres.json`,
  `connect-sink-postgres.json`) à poster sur `http://localhost:8083/connectors`.
- **PostgreSQL 16** avec un script d'init créant une table `clients`
  (source) et une table `clients_sink` (cible du connecteur sink).
- **MongoDB 7.0.7** en single-node standalone (pas de replica set, un seul noeud).
- **Kafka UI** (`provectuslabs/kafka-ui`) : vue cluster, topics, Connect,
  et métriques JMX (port 9999 des brokers).
- **Console JMX** : le choix le plus robuste en environnement Docker est
  **Hawtio + agent Jolokia** embarqué dans chaque broker Kafka (port
  8778). Alternative : `jconsole`/VisualVM depuis l'hôte sur les ports
  9101/9102/9103 (JMX RMI classique).
- **Console Redpanda** (`redpandadata/console`) : totalement compatible
  avec Kafka natif  KRAFT, fonctionne sans problème sur un cluster Kafka
  standard 3 brokers et sur Connect.

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

##### Lancement du 1er Kafka Connect : Source : 

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-source-postgres.json http://localhost:8083/connectors
```

Après l'exécution, vérifiez que le connecteur est bien actif :

Affichage de la liste des Kafka Connect :  
```bash
curl http://localhost:8083/connectors
```

Affichage en retour : 
```text
["postgres-source-clients"]
```

Affichage de l'état du Kafka Connect Source :  

```bash
curl http://localhost:8083/connectors/postgres-source-clients/status
```
Affichage en retour : 
```text
{"name":"postgres-source-clients","connector":{"state":"RUNNING","worker_id":"kafka-connect:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"kafka-connect:8083"}],"type":"source"}
```

##### Lancement du 2nd Kafka Connect : Sink cette fois : 

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-sink-postgres.json http://localhost:8083/connectors
```

Après l'exécution, vérifiez que les connecteurs sont bien actifs :

Affichage de la liste des Kafka Connect :  
```bash
curl http://localhost:8083/connectors
```

### Test de bout en bout :

Pour valider que le pipeline fonctionne réellement (Postgres → Kafka → Postgres), vous pouvez :

#### Consommer les messages produits par le connecteur source

```bash
docker exec -it kafka1 kafka-console-consumer --bootstrap-server localhost:19092 --topic pg-clients --from-beginning --max-messages 3
```

Remarque : Le message "Could not start Jolokia agent: java.net.BindException: Address already in use" est à ignorer (déjà lancé et opérationnel)

#### Vérifier que le connecteur sink a bien réinjecté les données dans la table clients_sink

```bash
docker exec -it postgres psql -U formation -d formation -c "SELECT * FROM clients_sink;"
```

##### Si les 3 clients (Alice, Bruno, Chloé) apparaissent dans clients_sink, le pipeline JDBC source→sink fonctionne de bout en bout.


#### Pour supprimer et recréer un connecteur si besoin (par exemple après une modification de config) :

```bash
curl -X DELETE http://localhost:8083/connectors/postgres-sink-clients
```

#### A savoir : le connecteur source garde son offset précédent (dernier id/timestamp lus) même après recréation, car Kafka Connect 3.8 stocke ces offsets dans un topic interne indépendant du topic de données, même s'il a été supprimé. 

Si le connecteur source pense avoir déjà lu les lignes existantes, il n'en réémet aucune : ceci peut occasionner un topic vide et donc la table sink vide.

Dans cette situation, le plus simple est de réinitialiser les offsets via l'API REST (Kafka Connect 3.8 supporte nativement cette opération) :


##### 1. Arrêter le connecteur source (requis avant de reset ses offsets)
```bash
curl -X PUT http://localhost:8083/connectors/postgres-source-clients/stop
```

##### 2. Réinitialiser ses offsets
```bash
curl -X DELETE http://localhost:8083/connectors/postgres-source-clients/offsets
```

##### 3. Redémarrer le connecteur
```bash
curl -X PUT http://localhost:8083/connectors/postgres-source-clients/resume
```

##### Vérification :
```bash
docker exec -it kafka1 kafka-console-consumer --bootstrap-server localhost:19092 --topic pg-clients --from-beginning --max-messages 3
```

On voit les 3 messages réapparaître (avec l'enveloppe schema/payload).

Le connecteur sink, déjà RUNNING, les consommera automatiquement dès qu'ils arrivent dans le topic.

```bash
docker exec -it postgres psql -U formation -d formation -c "SELECT * FROM clients_sink;"
```

#### A retenir donc : 
```text
les offsets de connecteurs source sont indépendants du contenu du topic Kafka : supprimer/recréer un topic ne suffit jamais à "repartir de zéro", il faut explicitement gérer les offsets stockés côté Connect. 
C'est une source d'erreur très fréquente en environnement de production.
```


#### Dans Hawtio, pour ajouter les connections vers nos 3 nœuds kafka : 

Dans le navigateur web : 

```text
http://localhost:8888/hawtio/jvm/connect
```
cliquer sur **Connect** puis ajouter une connexion distante vers `kafka1:8778`, `kafka2:8778`, `kafka3:8778` (chemin `/jolokia`) pour visualiser les MBeans JMX de chaque broker.

<img width="732" height="473" alt="Add connection hawtio" src="https://github.com/user-attachments/assets/f5c8cd99-ad81-479f-841d-acf60379982b" />


#### Points d'attention pour la suite

- Générer un nouveau `CLUSTER_ID` si vous dupliquez cet environnement pour
  plusieurs postes (`kafka-storage random-uuid`).
- Les ports hôtes 8080/8083/8090/8888/9092-9096/9101-9103/5432/27017
  doivent être libres sur la machine Ubuntu 24.04.
- Le sizing par défaut (heap JVM Kafka standard) convient pour un poste
  de formation ; ajustez `KAFKA_HEAP_OPTS` si RAM limitée.


### Rappel de l'accès aux interfaces

| Service            | URL                          |
|---------------------|-------------------------------|
| Kafka (client)       | `localhost:9092/9094/9096`   |
| Kafka Connect REST   | `http://localhost:8083`      |
| PostgreSQL           | `localhost:5432` (formation/formation) |
| MongoDB              | `localhost:27017` (formation/formation) |
| Kafka UI             | `http://localhost:8080`      |
| Hawtio (JMX)         | `http://localhost:8888/hawtio`      |
| Console Redpanda     | `http://localhost:8090`      |


#### Exemple d'utilisation du nœud mongoDB 
```bash
docker exec -it mongodb mongosh -u formation -p formation --authenticationDatabase admin
```
```bash
help
show databases;
use database_test
show collections
```

#### Exemple d'utilisation du nœud mongoDB via une chaîne de connexion complète
```bash
docker exec -it mongodb mongosh "mongodb://formation:formation@localhost:27017/?authSource=admin"
```

#### Exemple d'utilisation du nœud mongoDB depuis l'hôte (hors conteneur)

Si mongosh est installé sur la machine Ubuntu directement :
```bash
mongosh "mongodb://formation:formation@localhost:27017/?authSource=admin"
```

```javascript
show databases
use admin
show users
```


#### Kafka UI     

```bash
http://localhost:8080
```

#### Console Redpanda   

```bash
http://localhost:8090
```


### Have Fun :-)
