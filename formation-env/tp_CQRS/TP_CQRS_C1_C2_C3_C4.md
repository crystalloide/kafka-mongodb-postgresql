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

Vous devez voir les 5 paquets avec leurs versions.
```text
Package         Version
--------------- -------
dnspython       2.8.0
Faker           40.36.0
kafka-python    2.3.1
pip             26.2.1
psycopg2-binary 2.9.12
pymongo         4.17.0
python-dotenv   1.2.2

```

### 2.2 Préparation de Kafka et PostgreSQL

# Recréer le topic proprement
docker exec -it kafka1 /usr/bin/kafka-topics --bootstrap-server kafka1:19092 --delete --topic orders.events --if-exists
docker exec -it kafka1 /usr/bin/kafka-topics --bootstrap-server kafka1:19092 --create --topic orders.events --partitions 3 --replication-factor 3

# Nettoyer la table PostgreSQL s'il y a un résidu d'un TP précédent
docker exec -it postgres psql -U formation -d formation -c "DROP TABLE IF EXISTS orders;"
```

### 2.3 Configuration de Kafka Connect (Le lien vers l'Event Store)
Pour éviter les erreurs de parsing JSON avec Kafka Connect, nous allons utiliser un `StringConverter` couplé à un transformateur `HoistField`. Cela insérera l'événement JSON brut dans une colonne texte `event_payload` dans PostgreSQL.

Générez le fichier de configuration :
