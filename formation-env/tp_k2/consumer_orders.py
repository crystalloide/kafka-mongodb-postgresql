import json
import os

from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",  # lire depuis le début si aucun offset
    enable_auto_commit=True,        # commit automatique des offsets
)

print(
    f"Consommateur démarré sur topic={TOPIC}, group_id={GROUP_ID}. "
    "Ctrl+C pour arrêter."
)

try:
    for msg in consumer:
        key = msg.key
        event = msg.value
        partition = msg.partition
        offset = msg.offset

        print(
            f"[EVENT] partition={partition} offset={offset} key={key}\n"
            f"        event_type={event['event_type']} "
            f"order_id={event['payload']['order_id']} "
            f"customer_id={event['payload']['customer_id']} "
            f"total={event['payload']['total_amount']}"
        )

except KeyboardInterrupt:
    print("\nArrêt du consommateur.")
finally:
    consumer.close()