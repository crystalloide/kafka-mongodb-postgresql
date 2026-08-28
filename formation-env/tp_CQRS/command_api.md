# Explication détaillée du script : command_api.py 

Ce document détaille le code source du script Python implémentant l'**API d'Écriture (Command API)** basée sur Flask et Kafka . Elle reçoit les requêtes utilisateur (création et annulation de commandes) et produit les événements correspondants dans le topic Kafka `orders.events` .

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
import json
import os
from uuid import uuid4
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"

app = Flask(__name__)
```
- Importe Flask, les outils de sérialisation et la classe `KafkaProducer` . Configure l'application Flask et les paramètres Kafka .

### 2. Initialisation du KafkaProducer
```python
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
)
```
- Instancie le producteur Kafka avec sérialisation UTF-8/JSON
- acks="all" demande à Kafka d'attendre l'acquittement de tous les réplicas actuellement in-sync, ce qui renforce la garantie de durabilité de l'écriture.

### 3. Fonctions de construction des événements d'écriture
```python
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
```
- `build_order_created`: Formate l'événement de création de commande avec calcul automatique du montant total .
- `build_order_cancelled`: Formate l'événement d'annulation de commande .
- Remarque : **datetime.utcnow()** est déprécié depuis Python 3.12 : Python recommande désormais un datetime UTC aware, par exemple **datetime.now(timezone.utc)**
   - A modifier idéalement et remplacer par :
```
from datetime import datetime, timezone
datetime.now(timezone.utc).isoformat()
```

### 4. Endpoints de l'API Commandes (POST)
```python
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
```
- POST `/orders` : Valide la présence des données, génère un UUID de commande, construit l'événement `OrderCreated`, l'envoie dans Kafka avec la clé `order_id` et retourne une réponse 201 .
- POST `/orders/<order_id>/cancel` : Valide le `customer_id`, construit l'événement `OrderCancelled`, l'envoie dans Kafka et retourne un statut 200 .
- Remarque : L'endpoint **POST /orders/<order_id>/cancel** retourne immédiatement : **{"order_id": "...", "status": "CANCELLED"}** alors que le statut MongoDB n'a pas encore nécessairement été modifié : l'événement doit d'abord être consommé par **projector.py** : Cela illustre très bien la cohérence éventuelle
- A noter : 
```text
producer.send(...)
producer.flush()
```
signifie que l'envoi est asynchrone au niveau de send(), puis que flush() attend la fin des envois en attente avant de continuer.

### 5. Lancement de l'API Commandes
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```
- Lance l'API d'écriture sur le port `5000` .
