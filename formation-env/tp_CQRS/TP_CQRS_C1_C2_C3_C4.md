# Mini‑application avec le pattern CQRS - Command/Query/Responsibility/Segregation

## Présentation de CQRS
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

**Conséquence importante** : Les données lues et les données écrites ne sont plus forcément dans la même structure ni dans la même base, et la lecture devient souvent éventuellement cohérente (il y a un délai entre l’écriture et la mise à jour des vues de lecture).

---

## 2. Schéma de principe pour le TP CQRS (Kafka / PostgreSQL / MongoDB)

**Vue logique de l'architecture :**

**Python** => **API Command** => **kafka `orders.events`** => **kafka connect sink** => **PostgreSQL : table `orders`** (matérialise les écritures - **"Command side"**)
___
**Python** => **API Query** => **kafka `orders.events`** => **kafka consumer (Projector)** => **MongoDB** : **collection `orders_view`** (sert les lectures - **"Query Side"**)

### L’ensemble est typiquement CQRS :
- un modèle et une base pour l’écriture (PostgreSQL via Kafka Connect),
- un modèle et une base pour la lecture (MongoDB dénormalisé),
- et Kafka comme bus d’événements au centre.

---

## 0. Préparation de l'environnement

Ouvrez un terminal et activez votre environnement virtuel :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
python -m venv .venv && source .venv/bin/activate
cd tp_cqrs
```

Le fichier `.env` commun doit contenir ces variables :  

```text
KAFKA_BOOTSTRAP=localhost:9092,localhost:9094,localhost:9096
MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0
KAFKA_UI=http://localhost:8080
REDPANDA_CONSOLE=http://localhost:8090
KAFKA_CONNECT=http://localhost:8083
```

## TP C1 — Conception de l’architecture (Théorique)
**Command Side** : L’API reçoit les commandes (POST `/orders`), valide, et émet des événements (`OrderCreated`, `OrderCancelled`) dans Kafka. Kafka Connect sauvegarde cet historique d'événements dans PostgreSQL.  
**Query Side** : Un script de projection lit Kafka et met à jour en temps réel des documents agrégés dans MongoDB. L'API de lecture lit uniquement MongoDB.  

---

## TP C2 — Command Side
**Objectif** : mettre en place une API de création/annulation de commandes, publier sur `orders.events` et persister dans PostgreSQL.  

### 2.1 Script command_api.py — API Flask
Créez le fichier `command_api.py` :  

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
    "localhost:9092,localhost:9094,localhost:9096"
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

Lancer l’API (laisser ce terminal ouvert) :

```bash
python command_api.py
```

### Pré-requis terminal de commande :L

Ouvrez un nouveau terminal, activez l'environnement et assurez-vous d'avoir un environnement propre :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_cqrs
source ../.venv/bin/activate
```

- Fichier `requirements.txt` à (re)créer si non présent/renseigné :
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
flask
fastapi
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

Vous devez voir les paquets avec leurs versions.
```text
Package           Version
----------------- -------
annotated-doc     0.0.5
annotated-types   0.8.0
anyio             4.14.2
blinker           1.9.0
click             8.5.0
dnspython         2.8.0
Faker             40.37.0
fastapi           0.141.1
Flask             3.1.3
idna              3.19
itsdangerous      2.2.0
Jinja2            3.1.6
kafka-python      2.3.1
MarkupSafe        3.0.3
pip               26.2.1
psycopg2-binary   2.9.12
pydantic          2.13.4
pydantic_core     2.46.4
pymongo           4.17.0
python-dotenv     1.2.3
starlette         1.6.0
typing_extensions 4.16.0
typing-inspection 0.4.4
Werkzeug          3.1.8

```

### 2.2 Préparation de Kafka et PostgreSQL

```bash
# Recréer le topic proprement
docker exec -it kafka1 /usr/bin/kafka-topics --bootstrap-server kafka1:19092 --delete --topic orders.events --if-exists
```

```bash
docker exec -it kafka1 /usr/bin/kafka-topics --bootstrap-server kafka1:19092 --create --topic orders.events --partitions 3 --replication-factor 3
```

```bash
# Nettoyer la table PostgreSQL s'il y a un résidu d'un TP précédent
docker exec -it postgres psql -U formation -d formation -c "DROP TABLE IF EXISTS orders;"
```

### 2.3 Configuration de Kafka Connect (Le lien vers l'Event Store)
Pour éviter les erreurs de parsing JSON avec Kafka Connect, nous allons utiliser un `StringConverter` couplé à un transformateur `HoistField`. Cela insérera l'événement JSON brut dans une colonne texte `event_payload` dans PostgreSQL.

Générez le fichier de configuration :  

```bash
cat << 'EOF' > connect-sink-orders.json
{
  "name": "postgres-sink-orders",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "tasks.max": "1",
    "topics": "orders.events",
    "connection.url": "jdbc:postgresql://postgres:5432/formation",
    "connection.user": "formation",
    "connection.password": "formation",
    "insert.mode": "insert",
    "auto.create": "true",
    "table.name.format": "orders",
    "value.converter": "org.apache.kafka.connect.storage.StringConverter",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "transforms": "Hoist",
    "transforms.Hoist.type": "org.apache.kafka.connect.transforms.HoistField$Value",
    "transforms.Hoist.field": "event_payload"
  }
}
EOF
```

Déployez le connecteur sur Kafka Connect :

```bash
curl -X DELETE http://localhost:8083/connectors/postgres-sink-orders
curl -X POST -H "Content-Type: application/json" --data @connect-sink-orders.json http://localhost:8083/connectors
```

Vérifiez que le connecteur tourne :

```bash
curl -s http://localhost:8083/connectors/postgres-sink-orders/status | grep RUNNING
```

### 2.4 Test du Command Side

Créer une commande :

```bash
# 1. Créer la commande et stocker la réponse JSON
ORDER_RESPONSE=$(curl -s -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001", "items": [{"product_id": "P-001", "quantity": 1, "unit_price": 79.9}]}')

# Afficher la réponse pour vérifier
echo "Réponse reçue : $ORDER_RESPONSE"

# 2. Extraire proprement l'ID grâce à jq
ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.order_id')
echo "ID extrait : $ORDER_ID"

```

L'annuler :

```bash
# 3. Annuler la commande avec l'ID récupéré
curl -X POST http://localhost:5000/orders/$ORDER_ID/cancel \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001"}'
```

Vérifiez dans PostgreSQL que les événements sont bien sauvegardés :

```bash
docker exec -it postgres psql -U formation -d formation -c "SELECT * FROM orders;"
```
Vos événements bruts sont persistés fidèlement, offrant une piste d'audit parfaite pour les écritures.

Remarque : pour supprimer tous les événements dans PostgreSQL  (à ne pas faire ici) :

```bash
docker exec -it postgres psql -U formation -d formation -c DELETE FROM orders;"
```
---

## TP C3 — Query Side

**Objectif** : projeter les événements dans une vue de lecture dénormalisée dans MongoDB.

### 3.1 Script projector.py — projection dans MongoDB

Créez `projector.py` :  

```python
import json
import os
import uuid
from typing import Any
from dotenv import load_dotenv
from kafka import KafkaConsumer
from pymongo import MongoClient

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["training"]
orders_view = db["orders_view"]

# 1. Auto-détection de l'état de la base de données
is_empty = orders_view.count_documents({}) == 0

# 2. Assignation dynamique du groupe Kafka
if is_empty:
    # Base vide = nouveau groupe pour forcer la relecture de tout l'historique
    GROUP_ID = f"orders-projector-group-rebuild-{uuid.uuid4()}"
    print("🔄 Vue MongoDB vide détectée ! Rejeu automatique de l'historique en cours...")
else:
    # Base existante = on reprend la lecture normale
    GROUP_ID = "orders-projector-group"
    print("✅ Vue MongoDB existante. Reprise de la lecture classique...")

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
    orders_view.update_one({"order_id": order_id}, {"$set": doc}, upsert=True)

def apply_order_cancelled(event: dict[str, Any]) -> None:
    payload = event["payload"]
    orders_view.update_one(
        {"order_id": payload["order_id"]},
        {"$set": {"status": "CANCELLED", "last_event_id": event["event_id"], "last_event_at": event["occurred_at"]}},
        upsert=True,
    )

if __name__ == "__main__":
    print("Projecteur en écoute active... Ctrl+C pour arrêter.")
    try:
        for msg in consumer:
            event = msg.value
            event_type = event.get("event_type")
            if event_type == "OrderCreated":
                apply_order_created(event)
            elif event_type == "OrderCancelled":
                apply_order_cancelled(event)
    except KeyboardInterrupt:
        pass
    finally:
        mongo_client.close()
        consumer.close()
```

Lancer le projecteur dans un nouveau terminal :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
python -m venv .venv && source .venv/bin/activate
```

```bash
cd tp_cqrs
python projector.py
```

### 3.2 API de lecture query_api.py

Créez `query_api.py` :  

```python
import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0")
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
    docs = list(orders_view.find({"customer_id": customer_id}, {"_id": 0}))
    return jsonify(docs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```


Ouvrez un terminal et activez votre environnement virtuel :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
python -m venv .venv && source .venv/bin/activate
cd tp_cqrs
```

Lancer l'API dans un nouveau terminal :

```bash
python query_api.py
```

---

## TP C4 — Bout en bout et tests

**Générer des données en masse :**
Dans un terminal, lancez ce script pour simuler du trafic :  
Ouvrez un terminal et activez votre environnement virtuel :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
python -m venv .venv && source .venv/bin/activate
cd tp_cqrs
```

```bash
for i in $(seq 1 20); do
  curl -s -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d '{"customer_id": "CUST-'"$i"'", "items": [{"product_id": "P-001", "quantity": 1, "unit_price": 79.9}]}' > /dev/null
done
echo "20 commandes créées !"
```

**Vérifier le Command Side (Écriture - PostgreSQL)**

```bash
docker exec -it postgres psql -U formation -d formation -c "SELECT COUNT(*) FROM orders;"
```

**Vérifier le Query Side (Lecture - MongoDB)**

```bash
curl -s http://localhost:5001/customers/CUST-15/orders
```

**Le grand test de l'Event Sourcing CQRS (Rejeu) :**
Supprimez totalement la vue de lecture MongoDB :

```bash
# Spoiler alert : docker exec -it mongodb mongosh -u formation -p formation --authenticationDatabase admin --eval 'db.training.orders_view.drop()'   NE FONCTIONNERA PAS !!!
docker exec -it mongodb mongosh -u formation -p formation --authenticationDatabase admin --eval 'db.getSiblingDB("training").orders_view.drop()'
```

**La commande infaillible :**
Pour cibler proprement une base en mode script/non-interactif sans utiliser le raccourci **use**, il faut utiliser la méthode JavaScript native **db.getSiblingDB()** :

Dans le shell MongoDB (**mongosh**), la commande **use training** est un raccourci interactif (un helper de la console), pas une méthode JavaScript native.
Lorsqu'elle est passée dans une chaîne **--eval** non interactive, le contexte de la base de données ne bascule pas correctement pour les instructions qui suivent. 
Par conséquent, **db.orders_view.drop()** serait exécuté sur la base par défaut (test ou admin) : la bonne collection **training.orders_view** ne serait pas supprimée, et les données resteraient là et apparaîtraient lors du curl suivant.

**Vérifier le Query Side (Lecture - MongoDB)**

```bash
curl -s http://localhost:5001/customers/CUST-15/orders
```


**Arrêter le script `projector.py` (Ctrl+C) et le relancer :**

```bash
python projector.py
```

**Vérifier le Query Side (Lecture - MongoDB)**

```bash
curl -s http://localhost:5001/customers/CUST-15/orders
```

**Résultat :**  le script reconstruit **presque** instantanément toute la collection dans la base de données MongoDB à partir de l'historique contenu dans Kafka (via l'offset de lecture à 0 : `earliest`), prouvant la robustesse de cette approche et architecture.
