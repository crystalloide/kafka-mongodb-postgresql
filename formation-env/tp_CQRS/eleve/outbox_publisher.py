"""Outbox Publisher - version élève.

Lit les événements non publiés de PostgreSQL et les publie dans Kafka.
Le traitement demandé est volontairement simple : un seul publisher dans le handlab.
"""
import json
import os
import time

import psycopg
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://formation:formation@localhost:5432/training")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"


def build_producer():
    # TODO 1 : configurer la sérialisation JSON et les acquittements Kafka.
    raise NotImplementedError


def fetch_unpublished_events(conn, limit=20):
    # TODO 2 : récupérer les événements où published_at IS NULL.
    raise NotImplementedError


def mark_as_published(conn, event_id):
    # TODO 3 : renseigner published_at après confirmation de publication Kafka.
    raise NotImplementedError


def main():
    # TODO 4 : boucle de polling PostgreSQL -> Kafka -> marquage published_at.
    raise NotImplementedError


if __name__ == "__main__":
    main()
