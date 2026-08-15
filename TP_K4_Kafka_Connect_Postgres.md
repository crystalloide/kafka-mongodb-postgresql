## TP K4 — Kafka Connect avec PostgreSQL

**Durée** : 45 min

**Prérequis** :
- TP K1–K3 réalisés (cluster Kafka KRaft opérationnel, supervision OK).
- Environnement Docker Compose démarré :
  - Kafka 3.8.1 (3 brokers).
  - Kafka Connect (`formation/kafka-connect-jdbc:7.8.1`).
  - PostgreSQL 16 (user/db `formation` / `formation`).
- Fichiers de configuration déjà présents :
  - `connect-configs/connect-source-postgres.json`.
  - `connect-configs/connect-sink-postgres.json`.
- Kafka Connect REST accessible : `http://localhost:8083`.
- Extension **Thunder Client** installée dans VS Code (ou équivalent REST client).

## Objectifs

- Déployer un connecteur **source** JDBC captant les changements d’une table PostgreSQL vers un topic Kafka.
- Déployer un connecteur **sink** JDBC réinjectant les messages Kafka vers une table cible PostgreSQL.
- Utiliser l’API REST de Kafka Connect pour configurer, démarrer, vérifier le statut des connecteurs et observer le flux CDC de bout en bout.

---

## 0. Rappel de l’architecture Kafka Connect / PostgreSQL (5 min)

L’environnement de formation fournit :

- Un service **PostgreSQL 16** :
  - Table source `clients` (définie dans `postgres/init.sql`).
  - Table cible `clients_sink` pour le connecteur sink.
- Un service **Kafka Connect** :
  - Connecteur JDBC Source.
  - Connecteur JDBC Sink.
  - Configurations JSON prêtes à l’emploi dans `connect-configs/`.

Vue globale du pipeline :

1. **Source** : PostgreSQL (`clients`) → connecteur JDBC Source → topic Kafka `pg-clients`.
2. **Sink** : topic Kafka `pg-clients` → connecteur JDBC Sink → PostgreSQL (`clients_sink`).

Ce TP consiste à déployer ce pipeline et à le valider de bout en bout.

---

## 1. Déploiement du connecteur Source JDBC (15 min)

Objectif : publier les données de la table `clients` dans un topic Kafka `pg-clients`.

### 1.1 Découverte de la configuration source

Ouvrez le fichier `connect-configs/connect-source-postgres.json` dans VS Code.

Repérez les paramètres principaux :

- `name`: `postgres-source-clients`.
- `connector.class`: `io.confluent.connect.jdbc.JdbcSourceConnector`.
- `connection.url`: URL JDBC PostgreSQL (ex. `jdbc:postgresql://postgres:5432/formation`).
- `connection.user` / `connection.password`: `formation` / `formation`.
- `mode`: `timestamp+incrementing` ou `bulk` selon le modèle choisi.
- `table.whitelist`: `clients`.
- `topic.prefix`: `pg-` → topic `pg-clients`.

Expliquez brièvement :

- Le mode de capture (`bulk`, `incrementing`, `timestamp`, `timestamp+incrementing`).
- Le mapping table → topic (préfixe + nom de table).

### 1.2 Création du connecteur Source via l’API REST

Dans Thunder Client (VS Code) ou via curl, créez une requête **POST** :

- URL : `POST http://localhost:8083/connectors`.
- Headers : `Content-Type: application/json`.
- Body : contenu de `connect-configs/connect-source-postgres.json`.

Exemple en ligne de commande :

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-source-postgres.json http://localhost:8083/connectors
```

### 1.3 Vérification du connecteur Source

1. Liste des connecteurs :

```bash
curl http://localhost:8083/connectors
```

Réponse attendue (entre autres) :

```text
["postgres-source-clients"]
```

2. Statut du connecteur :

```bash
curl http://localhost:8083/connectors/postgres-source-clients/status
```

Réponse typique :

```json
{
  "name": "postgres-source-clients",
  "connector": {"state": "RUNNING", "worker_id": "kafka-connect:8083"},
  "tasks": [{"id": 0, "state": "RUNNING", "worker_id": "kafka-connect:8083"}],
  "type": "source"
}
```

3. Vérifier que le topic `pg-clients` reçoit des messages :

```bash
docker exec -it kafka1 kafka-console-consumer \
  --bootstrap-server localhost:19092 \
  --topic pg-clients \
  --from-beginning \
  --max-messages 3
```

Vous devez voir des messages JSON ou schema/payload correspondant aux lignes de la table `clients`.

---

## 2. Déploiement du connecteur Sink JDBC (15 min)

Objectif : consommer les messages du topic `pg-clients` et les réinjecter dans la table `clients_sink` de PostgreSQL.

### 2.1 Découverte de la configuration sink

Ouvrez `connect-configs/connect-sink-postgres.json` dans VS Code.

Repérez :

- `name`: `postgres-sink-clients`.
- `connector.class`: `io.confluent.connect.jdbc.JdbcSinkConnector`.
- `connection.url`: même URL JDBC vers PostgreSQL.
- `connection.user` / `connection.password`.
- `topics`: `pg-clients`.
- `auto.create`: `true` ou `false` (création automatique de la table cible).
- `insert.mode`: `insert` (ou `upsert` selon le choix).
- `table.name.format`: `clients_sink`.

Expliquez :

- Comment les enregistrements Kafka sont mappés vers la table cible.
- L’importance de la configuration du schéma pour `auto.create`.

### 2.2 Création du connecteur Sink via l’API REST

Dans Thunder Client ou via curl :

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect-configs/connect-sink-postgres.json http://localhost:8083/connectors
```

### 2.3 Vérification du connecteur Sink

1. Liste des connecteurs :

```bash
curl http://localhost:8083/connectors
```

Vous devez voir les deux connecteurs :

```text
["postgres-source-clients", "postgres-sink-clients"]
```

2. Statut du connecteur sink :

```bash
curl http://localhost:8083/connectors/postgres-sink-clients/status
```

Réponse attendue avec état `RUNNING` et au moins une tâche active.

3. Vérifier la table cible dans PostgreSQL :

```bash
docker exec -it postgres psql -U formation -d formation \
  -c "SELECT * FROM clients_sink;"
```

Les lignes de `clients` doivent apparaître dans `clients_sink` (par exemple les clients Alice, Bruno, Chloé du script d’init).

---

## 3. Exercice — Test CDC de bout en bout et gestion des offsets (15 min)

### 3.1 Test CDC bout en bout

1. Vérifiez le contenu de la table source `clients` :

```bash
docker exec -it postgres psql -U formation -d formation \
  -c "SELECT * FROM clients;"
```

2. Vérifiez le topic `pg-clients` :

```bash
docker exec -it kafka1 kafka-console-consumer \
  --bootstrap-server localhost:19092 \
  --topic pg-clients \
  --from-beginning \
  --max-messages 3
```

3. Vérifiez la table `clients_sink` :

```bash
docker exec -it postgres psql -U formation -d formation \
  -c "SELECT * FROM clients_sink;"
```

Si les mêmes lignes apparaissent, le pipeline Postgres → Kafka → Postgres fonctionne de bout en bout.

### 3.2 Gestion des offsets de connecteur source

Important : les **offsets** du connecteur source sont stockés dans un topic interne `_connect-offsets` et sont indépendants du contenu du topic de données.

Même si vous supprimez et recréez le topic `pg-clients`, le connecteur source se souviendra jusqu’où il a lu dans `clients` et ne réémettra pas les lignes déjà lues.

#### Cas d’école

- Vous supprimez le topic `pg-clients` et le recréez.
- Vous recréez le connecteur source avec la même configuration.
- Résultat : le topic peut rester vide, car le connecteur pense avoir déjà lu toutes les lignes de `clients`.

#### Réinitialiser les offsets du connecteur source

Pour forcer une relecture depuis le début :

1. Arrêter le connecteur source :

```bash
curl -X PUT http://localhost:8083/connectors/postgres-source-clients/stop
```

2. Supprimer ses offsets :

```bash
curl -X DELETE http://localhost:8083/connectors/postgres-source-clients/offsets
```

3. Redémarrer le connecteur :

```bash
curl -X PUT http://localhost:8083/connectors/postgres-source-clients/resume
```

4. Vérifier que les messages sont à nouveau produits dans `pg-clients` :

```bash
docker exec -it kafka1 kafka-console-consumer \
  --bootstrap-server localhost:19092 \
  --topic pg-clients \
  --from-beginning \
  --max-messages 3
```

Les messages réapparaissent, et le connecteur sink les consomme à nouveau pour remplir `clients_sink`.

### Questions de réflexion

- Pourquoi les offsets de connecteurs source sont‑ils indépendants du contenu du topic Kafka ?
- Quelles erreurs cela peut‑il provoquer en production (topics vides, tables sink non alimentées) ?
- Comment intégrer la réinitialisation des offsets dans un runbook d’exploitation ?

---

## 4. Synthèse pédagogique

- Kafka Connect permet d’implémenter facilement des **pipelines CDC** Postgres → Kafka → Postgres via des connecteurs JDBC source/sink.
- L’API REST de Connect (`/connectors`, `/status`, `/offsets`) est l’interface principale pour configurer, superviser et maintenir ces pipelines.
- La compréhension des **offsets** de connecteurs source est cruciale : elle évite les surprises lors de recréations de topics ou de connecteurs et prépare les stagiaires à la gestion des flux CDC en production.
