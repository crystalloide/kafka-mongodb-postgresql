import json
import os
import time

import psycopg
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://formation:formation@localhost:5432/formation")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"
POLL_INTERVAL_SECONDS = 1.0
BATCH_SIZE = 20


def build_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
    )


def fetch_unpublished_events(conn, limit=BATCH_SIZE):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_id, aggregate_id, payload
            FROM outbox_events
            WHERE published_at IS NULL
            ORDER BY occurred_at, event_id
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def mark_as_published(conn, event_id):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE outbox_events SET published_at = CURRENT_TIMESTAMP WHERE event_id = %s AND published_at IS NULL",
            (event_id,),
        )


def main():
    producer = build_producer()
    print("Outbox Publisher actif. Ctrl+C pour arrêter.")

    try:
        while True:
            with psycopg.connect(POSTGRES_DSN) as conn:
                events = fetch_unpublished_events(conn)
                if not events:
                    time.sleep(POLL_INTERVAL_SECONDS)
                    continue

                for event_id, aggregate_id, payload in events:
                    producer.send(
                        ORDERS_EVENTS_TOPIC,
                        key=str(aggregate_id),
                        value=payload,
                    ).get(timeout=10)
                    mark_as_published(conn, event_id)
                    conn.commit()
                    print(f"Publié: {event_id} ({payload['event_type']})")
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
