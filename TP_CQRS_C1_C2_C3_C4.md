## Mini‑application avec le pattern CQRS - Command/Query/Responsibility/Segregation

## Présentation de CQRS : 

CQRS est un pattern d’architecture qui sépare strictement les opérations d’écriture (commandes) des opérations de lecture (requêtes), chacune avec son propre modèle de données et parfois sa propre base.


## 1. Synthèse de l’approche CQRS

### Définition

**CQRS** (**Command Query Responsibility Segregation**) consiste à utiliser :
- un 1er modèle pour servir les commandes qui modifient l’état (create/update/delete)
- un 2nd modèle distinct pour servir les requêtes qui lisent l’état sans le modifier.

### Principe clé

Au lieu d’avoir un seul modèle/une seule base qui doit à la fois gérer la logique métier complexe et les requêtes de lecture, CQRS autorise :
- un modèle d’écriture optimisé pour la cohérence, les règles métier, les transactions ;
- un modèle de lecture optimisé pour la performance, la dénormalisation, les vues adaptées aux cas d’usage.

  
- **Conséquence importante** :
Les données lues et les données écrites ne sont plus forcément dans la même structure ni dans la même base, et la lecture devient souvent éventuellement cohérente (il y a un délai entre l’écriture et la mise à jour des vues de lecture)


## 2. Schéma de principe pour le TP CQRS (Kafka / PostgreSQL / MongoDB)

### Vue logique du Command Side et Query Side : 

___
**Dans le TP, on peut résumer l’architecture CQRS ainsi :**
___
**Python** => **API** => **kafka orders.events** => **kafka connect sink** => **PostgreSQL : table "orders"**		matérialise les **écritures**	(**"Command side"**)
___
**Python** => **API** => **kafka orders.events** => **kafka consummer** 	=> **MongoDB** : **collection "order_view"**	sert les **lectures**		(**"Query Side"**)


___
### Command Side (écriture)

#### 1°) API de commandes Python (command_api.py)

  - Endpoints POST /orders, POST /orders/{id}/cancel.
  - Valide la demande, construit des événements métier (OrderCreated, OrderCancelled) au format JSON.

#### 2°) Kafka — topic orders.events

  - L’API publie les événements sur le topic **orders.events** via **KafkaProducer** avec acks='all'.

#### 3°) Kafka Connect JDBC sink

 - Consomme les messages du topic **orders.events**
 - Insère les événements dans une table transactionnelle "orders" de PostgreSQL (source de vérité écriture).

___
### Query Side (lecture)

#### 4°) Projecteur Python (projector.py)

 - KafkaConsumer des messages dans le topic **orders.events**
 - Pour chaque événement, met à jour (upsert) un document dans MongoDB (orders_view) : état dénormalisé par commande (client, statut, total, articles…).

#### 5°) API de lecture Python (query_api.py)

- Endpoints GET /orders/{id}, GET /customers/{id}/orders.
- Ne parle qu’à MongoDB et renvoie la vue orders_view (JSON) sans jamais appeler PostgreSQL.
  
___
### Journal d’événements
  
Le topic orders.events est le flux d’événements métier qui permet :
 - d’alimenter PostgreSQL côté écriture (via Connect),
 - de construire et reconstruire la vue MongoDB côté lecture (via le projecteur).

___

### L’ensemble est typiquement CQRS :
- un modèle et une base pour l’écriture (PostgreSQL via Kafka Connect),
- un modèle et une base pour la lecture (MongoDB dénormalisé),
- et Kafka comme bus d’événements au centre.


___

## 3. Fonctionnement, avantages, inconvénients :

**Fonctionnement synthétique** :

**1°) Commandes (write model)**

- L’API reçoit une intention métier (créer/annuler une commande), applique des règles (validation) et publie un événement décrivant ce qui s’est passé.
- Kafka Connect sink persiste ces événements dans une base transactionnelle (orders dans PostgreSQL).

**2°) Requêtes (read model)**

- Un projecteur autonome consomme les mêmes événements et **maintient une vue de lecture** dans MongoDB sous une forme adaptée aux requêtes (orders_view).
- L’API de lecture se contente de lire cette vue (queries simples, sans logique métier lourde ni transactions complexes).

**3°) Rejeu / reconstruction**

- En cas de perte ou de changement de la vue, on peut rejouer les événements depuis Kafka (offset 0) pour reconstruire orders_view à partir du journal.

### Avantages : 

**- Modèles optimisés et séparés :**
  
On optimise le modèle de données dans PostgreSQL pour les écritures transactionnelles (index, contraintes) et MongoDB pour les lectures rapides, dénormalisées, adaptées aux besoins métier.

**- Scalabilité indépendante :**
  
Le Command Side (écritures) et le Query Side (lectures) peuvent être scalés différemment : par exemple plusieurs réplicas de l’API de lecture et du projecteur si les lectures explosent, sans toucher au chemin d’écriture.

**- Simplification des lectures :**
   
Les APIs de lecture interrogent directement des vues déjà agrégées (sans gros JOINs ni logique métier), ce qui simplifie le code et améliore les latences.

**- Meilleure séparation de responsabilités :**
  
Le code d’écriture reste focalisé sur les règles métier, la validation et les invariants ; le code de lecture reste focalisé sur l’ergonomie de consultation et le reporting.

**- Replay / audit :**
  
En gardant les événements dans Kafka, cela nous donne un journal auditable et rejouable pour reconstruire des vues ou analyser l’historique des commandes.


### Inconvénients et limites : 

- **Complexité accrue** :
  
Il y a donc maintenant :
- plusieurs modèles (write, read),
- plusieurs bases (PostgreSQL, MongoDB),
- des pipelines d’événements (Kafka, Connect, projecteur).
- La conception, la supervision et le debugging sont plus complexes qu’un simple CRUD monolithique.

- **Cohérence éventuelle** :
  
La vue MongoDB est mise à jour asynchrone depuis Kafka : une commande créée peut ne pas apparaître immédiatement dans GET /orders/{id} si le projecteur est en retard ou en panne. Il faut accepter une cohérence « eventual consistency ».

- **Synchronisation / échecs distribués** :
  
Il faut gérer les cas où :
- Kafka Connect est down,
- le projecteur a du lag ou des erreurs,
- des événements sont livrés en double ou en retard.
  
CQRS + événements introduisent de nouveaux modes de panne (offsets, replays, ordonnancement).

- **Coût opérationnel** :
  
Plus de composants = plus de monitoring, de sauvegardes, de procédures de reprise, de formation des équipes. Pour une application simple, CQRS peut être surdimensionné.

#### En résumé, l’architecture du TP illustre bien un CQRS pragmatique : 
- Kafka comme journal d’événements,
- PostgreSQL comme source de vérité écriture,
- MongoDB comme vue de lecture dénormalisée,
- deux APIs Python distinctes pour les commandes et les requêtes.

Adapté à une formation sur des systèmes où le volume, la complexité métier ou les besoins de projection justifient la séparation.

___

**Durée totale** : ≈ 2 h (C1 → C4)

**Prérequis** :
- TP K1–K4 réalisés :
  - Topics `orders.commands` et `orders.events` créés (3 partitions, RF=3, `min.insync.replicas=2`).
  - Producteur/consommateurs Python opérationnels (`kafka-python==2.3.1`).
  - Kafka Connect JDBC source/sink déployés (TP K4), PostgreSQL accessible.
- Environnement Docker Compose démarré :
  - Kafka 3.8.1 (KRaft, 3 brokers).
  - Kafka Connect (`formation/kafka-connect-jdbc:7.8.1`).
  - PostgreSQL 16 (user/db `formation` / `formation`).
  - MongoDB 7.0.7 (réplica set `rs0`, accessible depuis l’hôte).
- venv Python activé, dépendances installées :

```text
kafka-python==2.3.1
pymongo>=4.7,<5
psycopg2-binary
python-dotenv
faker
flask  # ou fastapi, selon choix du formateur
```

- Fichier `.env` commun aux TP CQRS, par exemple :

```text
# Endpoints Kafka / Postgres / MongoDB pour CQRS

KAFKA_BOOTSTRAP=localhost:9092,localhost:9094,localhost:9096

POSTGRES_DSN=postgresql://formation:formation@localhost:5432/formation

MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0

KAFKA_UI=http://localhost:8080
REDPANDA_CONSOLE=http://localhost:8090
KAFKA_CONNECT=http://localhost:8083
```

---

## 0. Nouveau terminal :

Dans un nouveau terminal :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
cd tp_cqrs
```

## TP C1 — Conception de l’architecture (20 min, semi‑théorique)

Objectif : poser la vision d’ensemble de la mini‑application CQRS avant de coder.

### 1.1 Schéma d’architecture (à dessiner ensemble)

Sur tableau / outil de dessin, construire le schéma suivant :

1. **Command Side** :
   - API commande (Python, Flask/FastAPI) expose des endpoints :
     - `POST /orders` → création de commande.
     - `POST /orders/{id}/cancel` → annulation de commande.
   - L’API publie des messages sur `orders.commands` (commandes) ou directement sur `orders.events` (événements métier validés).
   - Un **service de traitement** (script Python ou future brique métier) consomme `orders.commands`, applique les règles métier et publie des événements `OrderCreated`, `OrderCancelled` sur `orders.events`.
   - Le connecteur **Kafka Connect JDBC sink** persiste automatiquement les événements dans une table transactionnelle `orders` dans PostgreSQL (source de vérité écriture).

2. **Event Stream** :
   - Topic `orders.events` = flux d’événements métier (immutable) décrivant la vie des commandes.

3. **Query Side** :
   - Script Python `projector.py` consomme `orders.events` et maintient une vue dénormalisée dans MongoDB : collection `orders_view`.
   - Cette vue contient des documents par commande :

```json
{
  "order_id": "...",
  "customer_id": "...",
  "status": "CREATED" | "CANCELLED" | ...,
  "items": [ { "product_id": "...", "quantity": 1, "unit_price": 79.9 } ],
  "total_amount": 139.7,
  "last_event_id": "...",
  "last_event_at": "2026-08-15T12:34:56Z"
}
```

   - Une petite API de lecture (Flask/FastAPI) interroge **uniquement MongoDB** pour servir :
     - `GET /orders/{id}`.
     - `GET /customers/{id}/orders`.

### 1.2 Discussion guidée

Points à aborder avec les stagiaires :

- **Cohérence éventuelle** :
  - Le Command Side écrit dans PostgreSQL via Kafka Connect, le Query Side maintient une vue de lecture dans MongoDB.
  - La vue de lecture est reconstruite à partir des événements, avec un léger délai (cohérence « éventuelle », pas strictement immédiate).

- **Idempotence des projections** :
  - Le projecteur MongoDB doit pouvoir rejouer des événements déjà vus sans corrompre l’état.
  - Utiliser des opérations `upsert` (`update_one(..., upsert=True)`) et vérifier l’`event_id` pour éviter les doubles traitements.

- **Replay / reconstruction de vue** :
  - Si la collection `orders_view` est perdue ou corrompue, on peut vider MongoDB et rejouer tous les événements `orders.events` depuis l’offset 0 pour reconstruire la vue.
  - Kafka sert de « journal d’événements » durable qui permet de reconstituer l’état de lecture à tout moment.

---

## TP C2 — Command Side (45 min)

Objectif : mettre en place une API simple de création/annulation de commandes, qui publie des événements sur `orders.events` et laisse le connecteur JDBC sink les persister dans PostgreSQL.

### 2.1 Script `command_api.py` — API Flask

Créez un fichier `command_api.py` :

```python
import json
import os
from uuid import uuid4
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

ORDERS_EVENTS_TOPIC = "orders.events"

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
)


def build_order_created(order_id: str, customer_id: str, items: list[dict]) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "OrderCreated",
        "occurred_at": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": items,
            "total_amount": sum(i["quantity"] * i["unit_price"] for i in items),
        },
    }


def build_order_cancelled(order_id: str, customer_id: str) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "OrderCancelled",
        "occurred_at": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "order_id": order_id,
            "customer_id": customer_id,
        },
    }


@app.route("/orders", methods=["POST"])
def create_order():
    body = request.get_json(force=True)
    customer_id = body.get("customer_id")
    items = body.get("items", [])

    if not customer_id or not items:
        return jsonify({"error": "customer_id et items sont requis"}), 400

    order_id = str(uuid4())
    event = build_order_created(order_id, customer_id, items)

    # clé de partitionnement = order_id
    producer.send(ORDERS_EVENTS_TOPIC, key=order_id, value=event)
    producer.flush()

    return jsonify({"order_id": order_id, "status": "CREATED"}), 201


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    body = request.get_json(force=True)
    customer_id = body.get("customer_id")

    if not customer_id:
        return jsonify({"error": "customer_id est requis"}), 400

    event = build_order_cancelled(order_id, customer_id)

    producer.send(ORDERS_EVENTS_TOPIC, key=order_id, value=event)
    producer.flush()

    return jsonify({"order_id": order_id, "status": "CANCELLED"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 2.2 Vérifier la propagation dans PostgreSQL via Kafka Connect

1. S’assurer que le connecteur Kafka Connect **sink JDBC** est bien configuré pour consommer `orders.events` et insérer dans une table `orders` :
   - Dans `connect-sink-postgres.json`, vérifier :
     - `topics`: `orders.events`.
     - `table.name.format`: `orders`.

2. Vérifier dans Kafka Connect REST :

### Vidage de la la table cible clients_sink :
```bash
docker exec -it postgres psql -U formation -d formation \
  -c "DELETE FROM clients_sink;"
```

### 2.2 Création du connecteur Sink via l’API REST

Dans Thunder Client ou via curl :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_cqrs
curl -X POST -H "Content-Type: application/json" \
  --data @connect-sink-postgres.json http://localhost:8083/connectors
```


#### Si besoin : Pour supprimer et recréer un connecteur si besoin (par exemple après une modification de config) :

```bash
curl -X DELETE http://localhost:8083/connectors/postgres-sink-clients
```


### Vérification du connecteur Sink

Liste des connecteurs :

```bash
curl http://localhost:8083/connectors
```

Vous devez voir au moins le connecteur :

```text
["postgres-sink-orders"]
```

Statut du connecteur sink :

```bash
curl http://localhost:8083/connectors/postgres-sink-orders/status
```

Réponse attendue avec état `RUNNING` et au moins une tâche active.



3. Générer quelques commandes de test :

```bash
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001", "items": [
         {"product_id": "P-001", "quantity": 1, "unit_price": 79.9},
         {"product_id": "P-002", "quantity": 2, "unit_price": 29.9}
      ]}'
```

4. Annuler une commande :

```bash
curl -X POST http://localhost:5000/orders/<order_id>/cancel \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001"}'
```

5. Vérifier la table `orders` dans PostgreSQL :

```bash
docker exec -it postgres psql -U formation -d formation \
  -c "SELECT * FROM orders;"
```

Les événements `OrderCreated` et `OrderCancelled` doivent être présents (selon le schéma défini par le connecteur sink).

### 2.3 Points de discussion

- Le Command Side **ne lit pas** dans MongoDB : il se contente d’émettre des événements et de persister l’état transactionnel.
- La table `orders` est la **source de vérité** pour les écritures, Kafka Connect se charge de l’alimentation.

---

## TP C3 — Query Side (45 min)

Objectif : projeter les événements `orders.events` dans une vue de lecture MongoDB, et exposer une API de lecture qui interroge uniquement cette vue.

### 3.1 Script `projector.py` — projection dans MongoDB

Créez le fichier `projector.py` :

```python
import json
import os
from typing import Any

from dotenv import load_dotenv
from kafka import KafkaConsumer
from pymongo import MongoClient

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

ORDERS_EVENTS_TOPIC = "orders.events"
GROUP_ID = "orders-projector-group"

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0",
)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["training"]
orders_view = db["orders_view"]


consumer = KafkaConsumer(
    ORDERS_EVENTS_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)


def apply_order_created(event: dict[str, Any]) -> None:
    payload = event["payload"]
    order_id = payload["order_id"]

    doc = {
        "order_id": order_id,
        "customer_id": payload["customer_id"],
        "status": "CREATED",
        "items": payload["items"],
        "total_amount": payload["total_amount"],
        "last_event_id": event["event_id"],
        "last_event_at": event["occurred_at"],
    }

    orders_view.update_one(
        {"order_id": order_id},
        {"$set": doc},
        upsert=True,
    )


def apply_order_cancelled(event: dict[str, Any]) -> None:
    payload = event["payload"]
    order_id = payload["order_id"]

    orders_view.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "status": "CANCELLED",
                "last_event_id": event["event_id"],
                "last_event_at": event["occurred_at"],
            }
        },
        upsert=True,
    )


if __name__ == "__main__":
    print(
        f"Projecteur démarré sur topic={ORDERS_EVENTS_TOPIC}, group_id={GROUP_ID}. "
        "Ctrl+C pour arrêter."
    )

    try:
        for msg in consumer:
            event = msg.value
            event_type = event.get("event_type")

            if event_type == "OrderCreated":
                apply_order_created(event)
            elif event_type == "OrderCancelled":
                apply_order_cancelled(event)
            else:
                print(f"[WARN] Événement inconnu : {event_type}")

    except KeyboardInterrupt:
        print("\nArrêt du projecteur.")
    finally:
        mongo_client.close()
        consumer.close()
```

### 3.2 API de lecture `query_api.py`

Créez un fichier `query_api.py` :

```python
import os

from flask import Flask, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0",
)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["training"]
orders_view = db["orders_view"]

app = Flask(__name__)


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    doc = orders_view.find_one({"order_id": order_id}, {"_id": 0})
    if not doc:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(doc)


@app.route("/customers/<customer_id>/orders", methods=["GET"])
def get_customer_orders(customer_id: str):
    docs = list(
        orders_view.find({"customer_id": customer_id}, {"_id": 0})
    )
    return jsonify(docs)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```

### 3.3 Vérifications

1. Lancer le projecteur :

```bash
python projector.py
```

2. Générer quelques commandes via `command_api.py` (TP C2). 

3. Interroger l’API de lecture :

```bash
curl http://localhost:5001/orders/<order_id>
curl http://localhost:5001/customers/CUST-1001/orders
```

Les réponses doivent être servies **exclusivement depuis MongoDB**, sans requête vers PostgreSQL.

### 3.4 Discussion

- Le Query Side est découplé de la persistance transactionnelle : il ne connaît que les événements et la vue de lecture.
- Il est possible d’ajouter de nouvelles vues dérivées (par exemple `customer_view`) en rejouant les mêmes événements.

---

## TP C4 — Bout en bout et supervision (10–20 min)

Objectif : faire tourner la mini‑application CQRS de bout en bout et visualiser le flux dans les outils de supervision.

### 4.1 Scénario complet

1. Services à lancer :
   - `command_api.py` (port 5000).
   - `projector.py` (consommateur sur `orders.events`).
   - `query_api.py` (port 5001).
   - Assurez‑vous que Kafka Connect source/sink pour `orders.events` → `orders` est **RUNNING**.

2. Injecter 20 commandes :

Vous pouvez écrire un petit script `bulk_orders.py` ou utiliser un outil (Faker) pour générer 20 commandes :

```bash
for i in $(seq 1 20); do
  curl -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d '{"customer_id": "CUST-'"$i"'", "items": [
           {"product_id": "P-001", "quantity": 1, "unit_price": 79.9}
        ]}'
done
```

3. Vérifier dans Kafka UI :
   - Topic `orders.events` : nombre de messages, partitions utilisées.
   - Consumer groups :
     - Groupe du projecteur (`orders-projector-group`) et son lag.

4. Vérifier dans Redpanda Console :
   - Topic `orders.events` : contenu des messages (JSON `OrderCreated`, `OrderCancelled`).
   - Consumer groups : lags et offsets.

5. Vérifier dans PostgreSQL :

```bash
docker exec -it postgres psql -U formation -d formation \
  -c "SELECT COUNT(*) FROM orders;"
```

6. Vérifier dans MongoDB :

```bash
docker exec -it mongodb mongosh \
  -u formation -p formation --authenticationDatabase admin \
  --eval 'db.training.orders_view.countDocuments()'
```

Le nombre de documents `orders_view` doit correspondre au nombre de commandes créées (modulo annulations). 

### 4.2 Discussion finale

- **Rejeu depuis Kafka** :
  - Si vous supprimez la collection `orders_view` :

```bash
docker exec -it mongodb mongosh \
  -u formation -p formation --authenticationDatabase admin \
  --eval 'db.training.orders_view.drop()'
```

  - Puis que vous relancez `projector.py` avec `auto_offset_reset="earliest"`, il rejouera tous les événements depuis l’offset 0 et reconstruira la vue.

- **Séparation des responsabilités** :
  - Le Command Side ne fait que valider les commandes et publier des événements.
  - Le Query Side se concentre sur la lecture performante et la dénormalisation.

- **Évolution** :
  - On peut ajouter de nouvelles projections (par client, par produit, par jour) en consommant le même flux d’événements.

---

## Synthèse du bloc CQRS

- Kafka sert de **journal d’événements** : toutes les modifications métier sont enregistrées dans `orders.events`.
- PostgreSQL est la **source de vérité transactionnelle** (Command Side) via Kafka Connect.
- MongoDB héberge des **vues de lecture dénormalisées**, construites par projection, optimisées pour les requêtes de lecture.
- La séparation Command/Query permet d’adapter indépendamment les modèles de données, les performances et les API côté écriture et lecture, tout en s’appuyant sur le même flux d’événements.
