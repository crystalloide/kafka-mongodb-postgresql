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

is_empty = orders_view.count_documents({}) == 0
if is_empty:
    GROUP_ID = f"orders-projector-group-rebuild-{uuid.uuid4()}"
    print("🔄 Vue MongoDB vide : lecture depuis le plus ancien offset encore disponible.")
else:
    GROUP_ID = "orders-projector-group"
    print("✅ Vue MongoDB existante : reprise du groupe standard.")

consumer = KafkaConsumer(
    ORDERS_EVENTS_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)


def apply_event(event: dict[str, Any]) -> None:
    event_type = event["event_type"]
    payload = event["payload"]
    order_id = payload["order_id"]
    version = int(event["aggregate_version"])

    current = orders_view.find_one({"order_id": order_id})
    current_version = int(current.get("last_event_version", 0)) if current else 0

    # Idempotence + protection contre un événement plus ancien.
    if version <= current_version:
        print(f"Événement ignoré: {event['event_id']} v{version} <= v{current_version}")
        return

    if event_type == "OrderCreated":
        new_doc = {
            "order_id": order_id,
            "customer_id": payload["customer_id"],
            "status": "CREATED",
            "items": payload["items"],
            "total_amount": payload["total_amount"],
            "last_event_id": event["event_id"],
            "last_event_at": event["occurred_at"],
            "last_event_version": version,
        }
        orders_view.replace_one({"order_id": order_id}, new_doc, upsert=True)

    elif event_type == "OrderCancelled":
        if current is None:
            new_doc = {
                "order_id": order_id,
                "customer_id": payload["customer_id"],
                "status": "CANCELLED",
                "last_event_id": event["event_id"],
                "last_event_at": event["occurred_at"],
                "last_event_version": version,
            }
            orders_view.insert_one(new_doc)
        else:
            orders_view.update_one(
                {"order_id": order_id},
                {"$set": {
                    "status": "CANCELLED",
                    "last_event_id": event["event_id"],
                    "last_event_at": event["occurred_at"],
                    "last_event_version": version,
                }},
            )
    else:
        print(f"Type d'événement inconnu: {event_type}")
        return

    print(f"Projeté: {event_type} {order_id} v{version}")


if __name__ == "__main__":
    print("Projecteur en écoute active... Ctrl+C pour arrêter.")
    try:
        for msg in consumer:
            try:
                apply_event(msg.value)
            except (KeyError, TypeError, ValueError) as exc:
                print(f"Événement invalide ignoré: {exc}")
    except KeyboardInterrupt:
        pass
    finally:
        mongo_client.close()
        consumer.close()
