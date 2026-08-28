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