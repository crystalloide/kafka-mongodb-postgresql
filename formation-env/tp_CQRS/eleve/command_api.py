"""Command API - version élève.

Point de départ : le script du TP existant.
Objectif : déplacer la logique d'écriture dans PostgreSQL et créer un événement
outbox dans la même transaction.
"""
import json
import os
from uuid import uuid4
from datetime import datetime, timezone

import psycopg
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://formation:formation@localhost:5432/training")
ORDERS_EVENTS_TOPIC = "orders.events"
app = Flask(__name__)

# La Command API ne publiera plus directement dans Kafka.
# Kafka sera alimenté par outbox_publisher.py.


def get_postgres_connection():
    """TODO 1 : retourner une connexion PostgreSQL."""
    raise NotImplementedError


def validate_items(items):
    """TODO 2 : vérifier que la liste est non vide et que quantity/unit_price sont valides."""
    raise NotImplementedError


def create_order_in_transaction(customer_id, items):
    """TODO 3 : persister orders, order_items et outbox_events dans UNE transaction."""
    raise NotImplementedError


@app.route("/orders", methods=["POST"])
def create_order():
    """TODO 4 : appeler create_order_in_transaction() et retourner HTTP 201."""
    raise NotImplementedError


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    """TODO 5 : vérifier la commande, l'annuler en PostgreSQL et créer OrderCancelled."""
    raise NotImplementedError


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
