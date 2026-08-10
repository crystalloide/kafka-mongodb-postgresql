### TPs Formation Python / Kafka / MongoDB / CQRS (2 jours)

Environnement : Docker Compose sur Ubuntu 24.04, Kafka 3.8.1 (KRaft, 3 nœuds controller/broker), Kafka Connect (source/sink PostgreSQL 16), MongoDB 7.0.7 (1 nœud), Kafka UI, Hawtio (JMX), Redpanda Console.
Client Python : `kafka-python==2.3.1`, `pymongo` (≥4.7 recommandé pour MongoDB 7.0), IDE : VS Code (extensions Python, Docker, MongoDB, YAML).

> Note de compatibilité vérifiée : PyMongo doit être en version **4.7 ou supérieure** pour un support complet de MongoDB 7.0 (versions antérieures fonctionnent en mode dégradé ⊛, sans les nouvelles fonctionnalités serveur). `kafka-python 2.3.1` est la dernière release maintenue du client pur-Python et communique en protocole Kafka standard, compatible avec un broker 3.8.1 en mode KRaft (pas de dépendance ZooKeeper requise côté client).

---

###  0. Préparation VS Code & environnement Python (30 min, transverse)

Objectif : chaque stagiaire a un environnement fonctionnel avant de commencer les TP techniques.

- Vérifier que tous les conteneurs sont `Up (healthy)` :
```bash
docker compose ps
```
- Installation python :
```bash
sudo apt update
sudo apt install python-is-python3
```
Vérifiez ensuite :
```bash
python --version
```
- Fichier `requirements.txt` à créer
```bash
vi requirements.txt
```
- avec le contenu suivant :
```bash
kafka-python==2.3.1
pymongo>=4.7,<5
psycopg2-binary
python-dotenv
faker
```

- Créer un venv dédié :
```bash
python -m venv .venv && source .venv/bin/activate
```

- Mettre à jour pip (évite des erreurs de résolution de dépendances) :
```bash
pip install --upgrade pip
```

- Installer les paquets :
```bash
pip install -r requirements.txt
```

- Vérifier l'installation :
```bash
pip list
```

Vous devez voir les 5 paquets avec leurs versions.


- Extensions VS Code : Python (Microsoft), Docker, MongoDB for VS Code, YAML, Thunder Client (pour tester Kafka Connect REST API).

- Fichier `.env` avec les endpoints : `KAFKA_BOOTSTRAP=localhost:9092,localhost:9093,localhost:9094`, `MONGO_URI=mongodb://localhost:27017`, `KAFKA_UI=http://localhost:8080`, `HAWTIO=http://localhost:8081/hawtio`, `REDPANDA_CONSOLE=http://localhost:8082`.

- Vérification rapide avec script `check_env.py` qui teste la connexion Kafka (métadonnées cluster) et MongoDB (`ping`) et affiche un résumé OK/KO.

---

###  1. Bloc MongoDB — 0,75 jour (≈ 3h de pratique)

### TP M1 — Prise en main & driver PyMongo (45 min)
- Connexion via `MongoClient`, exploration `list_database_names()`, création d'une base `training`.
- CRUD de base sur une collection `products` : `insert_one`/`insert_many`, `find`/`find_one` avec filtres, `update_one`/`update_many` (`$set`, `$inc`), `delete_many`.
- Exercice : charger 500 documents produits générés avec `Faker`, puis écrire 5 requêtes de filtrage (plage de prix, regex sur nom, tri, pagination `skip/limit`).

### TP M2 — Modélisation de documents & agrégation (45 min)
- Comparaison modèle embarqué vs référencé (ex. commandes + lignes de commande).
- Pipeline d'agrégation : `$match`, `$group`, `$project`, `$sort`, `$lookup` (jointure entre `orders` et `customers`).
- Exercice guidé : calculer le chiffre d'affaires par client et par mois à partir d'une collection `orders` préchargée.

### TP M3 — Index, performance et validation de schéma (45 min)
- Création d'index simples, composés, et `explain()` pour observer `COLLSCAN` vs `IXSCAN`.
- Mise en place d'un schéma de validation JSON Schema sur une collection (`$jsonSchema`) pour illustrer la gouvernance de données (thème gouvernance/qualité des données).
- Exercice : optimiser une requête lente en ajoutant l'index adéquat et mesurer le gain avec `explain(executionStats)`.

### TP M4 — Change Streams avec PyMongo (45 min)
- Ouverture d'un `watch()` sur une collection pour capter les insertions/mises à jour en temps réel.
- Exercice : un script producteur insère des documents, un script consommateur affiche les événements du Change Stream — brique de préparation conceptuelle au CQRS/CDC de l'après-midi 2.

**Supervision associée** : les stagiaires observent les collections/index via **MongoDB for VS Code** ou `mongosh` en parallèle des scripts Python.

---

###  2. Bloc Kafka — 0,75 jour (≈ 3h de pratique)

### TP K1 — Cluster KRaft, topics et CLI (30 min)
- Découverte des 3 nœuds via **Kafka UI** (brokers, controllers, partitions, ISR).
- Création d'un topic (`kafka-topics.sh` ou UI) avec réplication factor 3 et discussion sur `min.insync.replicas`, `acks`.
- Exercice : créer 2 topics (`orders.commands`, `orders.events`) avec 3 partitions chacun.

### TP K2 — Producteur/Consommateur avec kafka-python 2.3.1 (60 min)
- `KafkaProducer` : sérialisation JSON, clé de partitionnement, `acks='all'`, gestion des callbacks (`on_send_success`/`on_send_error`).
- `KafkaConsumer` : groupes de consommateurs, `auto_offset_reset`, commit manuel vs automatique, désérialisation JSON.
- Exercice : producteur qui publie des événements `OrderCreated` sur `orders.events`; deux consommateurs dans le même groupe pour observer le rééquilibrage des partitions (`ConsumerRebalanceListener`).

### TP K3 — Supervision via Hawtio/JMX et Redpanda Console (30 min)
- Connexion à **Hawtio** pour explorer les MBeans JMX d'un broker (débit, latence de réplication, `UnderReplicatedPartitions`).
- Utilisation de la **Redpanda Console** pour visualiser messages, schémas et consumer groups en parallèle de Kafka UI (comparaison des deux outils).
- Exercice : provoquer volontairement un retard de consommation (consumer lag) et l'observer dans les deux consoles.

### TP K4 — Kafka Connect avec PostgreSQL (45 min)
- Déploiement d'un connecteur **source** (Debezium ou JDBC Source) captant les changements d'une table PostgreSQL vers un topic Kafka.
- Déploiement d'un connecteur **sink** JDBC réinjectant des messages Kafka vers une autre table PostgreSQL.
- Exercice : via l'API REST de Kafka Connect (testée avec Thunder Client dans VS Code), configurer, démarrer, vérifier le statut (`GET /connectors/{name}/status`) et observer le flux CDC de bout en bout.

---

###  3. Bloc CQRS — 0,5 jour (≈ 2h)

### Objectif applicatif
Construire une mini-application illustrant le pattern CQRS : le **côté Commande** écrit les événements métier dans Kafka et persiste l'état transactionnel dans PostgreSQL (via Kafka Connect), tandis que le **côté Requête** consomme les événements Kafka pour construire une vue dénormalisée dans MongoDB, optimisée pour la lecture.

### TP C1 — Conception de l'architecture (20 min, semi-théorique)
- Schéma d'architecture : API commande (Python) → topic `orders.commands` → service de traitement → topic `orders.events` → (a) sink PostgreSQL (source de vérité) et (b) consommateur Python qui projette dans MongoDB (`orders_view`).
- Discussion : cohérence éventuelle, idempotence des projections, rejeu (`replay`) depuis Kafka pour reconstruire une vue de lecture.

### TP C2 — Command Side (45 min)
- Script Python exposant une fonction `create_order(customer_id, items)` qui valide la commande et publie un événement `OrderCreated` (JSON) dans `orders.events` via `KafkaProducer`.
- Le connecteur **sink JDBC** (déjà configuré en TP K4) persiste automatiquement les événements dans une table `orders` PostgreSQL — illustrant la responsabilité "écriture".
- Exercice : ajouter une commande `CancelOrder` et vérifier sa propagation dans PostgreSQL.

### TP C3 — Query Side (45 min)
- Script Python (`projector.py`) : `KafkaConsumer` sur `orders.events`, qui met à jour un document MongoDB par commande (`upsert`) avec une vue agrégée (client, statut, total, articles).
- Exercice : construire une petite API (Flask/FastAPI, ou simple script) qui interroge **uniquement MongoDB** pour répondre à des requêtes de lecture (`GET /orders/{id}`, `GET /customers/{id}/orders`), démontrant la séparation totale lecture/écriture.

### TP C4 — Bout en bout et supervision (10-20 min, restitution)
- Scénario complet : injecter 20 commandes via le Command Side, vérifier dans **Kafka UI** le débit des topics, dans **Redpanda Console** le contenu des messages, dans PostgreSQL la table transactionnelle, et dans MongoDB la vue de lecture reconstruite.
- Discussion finale : que se passe-t-il si on rejoue les événements depuis l'offset 0 sur un nouveau topic MongoDB de projection (reconstruction de vue) ?

---

###  Répartition horaire indicative (jour 2, après 1 jour de théorie)

| Créneau | Contenu | Durée |
|---|---|---|
| Matin | TP M1 → M4 (MongoDB) | 3h |
| Début après-midi | TP K1 → K4 (Kafka) | 3h |
| Fin après-midi | TP C1 → C4 (CQRS) | 2h |

###  Livrables à préparer par le formateur
- Jeux de données `Faker` préchargés (clients, produits, commandes) pour éviter de perdre du temps en saisie manuelle.
- Fichiers `docker-compose.override.yml` ou scripts `init` pour pré-créer les topics et la base PostgreSQL cible du connecteur sink.
- Corrigés Python pour chaque TP (dossier `solutions/`) et README avec commandes de vérification rapide (`docker compose logs`, `curl localhost:8083/connectors`).
- Une check-list de dépannage courant : ports déjà utilisés, `advertised.listeners` mal configuré pour un accès depuis l'hôte, réplication factor > nombre de brokers disponibles.
