import json
import os
from typing import Any

from dotenv import load_dotenv
from kafka import KafkaConsumer
from pymongo import MongoClient

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"
GROUP_ID = "orders-projector-group"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0")

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
    orders_view.update_one({"order_id": order_id}, {"$set": doc}, upsert=True)

def apply_order_cancelled(event: dict[str, Any]) -> None:
    payload = event["payload"]
    orders_view.update_one(
        {"order_id": payload["order_id"]},
        {"$set": {"status": "CANCELLED", "last_event_id": event["event_id"], "last_event_at": event["occurred_at"]}},
        upsert=True,
    )

if __name__ == "__main__":
    print("Projecteur démarré... Ctrl+C pour arrêter.")
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