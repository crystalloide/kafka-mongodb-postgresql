import json
import os
from typing import Collection

from dotenv import load_dotenv
from kafka import KafkaConsumer, ConsumerRebalanceListener, TopicPartition

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"


class RebalanceLogger(ConsumerRebalanceListener):
    """Listener pour afficher les partitions révoquées/assignées."""

    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer

    def on_partitions_revoked(self, revoked: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions révoquées :", list(revoked))

    def on_partitions_assigned(self, assigned: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions assignées :", list(assigned))


consumer = KafkaConsumer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

listener = RebalanceLogger(consumer)

consumer.subscribe([TOPIC], listener=listener)

print(
    f"Consommateur avec listener démarré sur topic={TOPIC}, group_id={GROUP_ID}. "
    "Ctrl+C pour arrêter."
)

try:
    for msg in consumer:
        key = msg.key
        event = msg.value
        partition = msg.partition
        offset = msg.offset

        print(
            f"[EVENT] partition={partition} offset={offset} key={key} "
            f"order_id={event['payload']['order_id']}"
        )

except KeyboardInterrupt:
    print("\nArrêt du consommateur.")
finally:
    consumer.close()