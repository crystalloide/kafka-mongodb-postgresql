"""Projector - version élève.

Le script actuel du TP peut être conservé comme base.
Travail demandé : rendre la projection idempotente et sensible à aggregate_version.
"""
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

# Conserver la logique de reconstruction du script initial.
is_empty = orders_view.count_documents({}) == 0
GROUP_ID = f"orders-projector-group-rebuild-{uuid.uuid4()}" if is_empty else "orders-projector-group"

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
    """TODO : appliquer un événement uniquement s'il est plus récent que la version présente."""
    raise NotImplementedError


if __name__ == "__main__":
    print("Projecteur en écoute active... Ctrl+C pour arrêter.")
    try:
        for msg in consumer:
            apply_event(msg.value)
    except KeyboardInterrupt:
        pass
    finally:
        mongo_client.close()
        consumer.close()
