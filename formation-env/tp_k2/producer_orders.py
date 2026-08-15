import json
import os
from uuid import uuid4
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",  # attente de l'ack de tous les ISR (durabilité forte)
)


def on_send_success(record_metadata):
    print(
        f"[SUCCESS] topic={record_metadata.topic} "
        f"partition={record_metadata.partition} offset={record_metadata.offset}"
    )


def on_send_error(ex):
    print(f"[ERROR] envoi sur {TOPIC} : {ex}")


def build_order_created(customer_id: str, items: list[dict]) -> dict:
    """Construit un événement OrderCreated en JSON.

    items: liste de dicts {"product_id", "quantity", "unit_price"}.
    """
    return {
        "event_id": str(uuid4()),
        "event_type": "OrderCreated",
        "occurred_at": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "order_id": str(uuid4()),
            "customer_id": customer_id,
            "items": items,
            "total_amount": sum(
                i["quantity"] * i["unit_price"] for i in items
            ),
        },
    }


if __name__ == "__main__":
    print(f"Envoi de 10 événements OrderCreated sur {TOPIC}...")

    for i in range(10):
        customer_id = f"CUST-{1000 + i}"
        items = [
            {"product_id": "P-001", "quantity": 1, "unit_price": 79.9},
            {"product_id": "P-002", "quantity": 2, "unit_price": 29.9},
        ]
        event = build_order_created(customer_id, items)

        # Clé de partitionnement = customer_id pour conserver l'ordre
        future = producer.send(TOPIC, key=customer_id, value=event)
        future.add_callback(on_send_success)
        future.add_errback(on_send_error)

    # Flush pour s'assurer que tout est envoyé
    producer.flush()
    producer.close()

    print("Terminé.")