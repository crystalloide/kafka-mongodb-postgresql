import json
import os
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from datetime import datetime, timezone

import psycopg
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://formation:formation@localhost:5432/formation")

app = Flask(__name__)


def get_connection():
    return psycopg.connect(POSTGRES_DSN)


def validate_items(items):
    if not isinstance(items, list) or not items:
        return "items doit être une liste non vide"

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return f"items[{index}] doit être un objet"
        product_id = item.get("product_id")
        if not product_id:
            return f"items[{index}].product_id est requis"
        try:
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            return f"items[{index}].quantity doit être un entier"
        if quantity <= 0:
            return f"items[{index}].quantity doit être > 0"
        try:
            price = Decimal(str(item.get("unit_price")))
        except (InvalidOperation, ValueError, TypeError):
            return f"items[{index}].unit_price doit être numérique"
        if price < 0:
            return f"items[{index}].unit_price doit être >= 0"

    return None


def create_order_in_transaction(customer_id, items):
    order_id = uuid4()
    occurred_at = datetime.now(timezone.utc)
    event_id = uuid4()
    version = 1

    normalized_items = [
        {
            "product_id": item["product_id"],
            "quantity": int(item["quantity"]),
            "unit_price": float(item["unit_price"]),
        }
        for item in items
    ]
    total_amount = sum(item["quantity"] * item["unit_price"] for item in normalized_items)

    event = {
        "event_id": str(event_id),
        "event_type": "OrderCreated",
        "occurred_at": occurred_at.isoformat(),
        "aggregate_version": version,
        "payload": {
            "order_id": str(order_id),
            "customer_id": customer_id,
            "items": normalized_items,
            "total_amount": total_amount,
        },
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM customers WHERE customer_id = %s", (customer_id,))
            if cur.fetchone() is None:
                raise ValueError("Client inconnu")

            cur.execute(
                """
                INSERT INTO orders (order_id, customer_id, status, version, created_at, updated_at)
                VALUES (%s, %s, 'CREATED', %s, %s, %s)
                """,
                (order_id, customer_id, version, occurred_at, occurred_at),
            )

            cur.executemany(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (order_id, item["product_id"], item["quantity"], item["unit_price"])
                    for item in normalized_items
                ],
            )

            cur.execute(
                """
                INSERT INTO outbox_events
                    (event_id, aggregate_id, aggregate_version, event_type, occurred_at, payload)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    event_id,
                    order_id,
                    version,
                    "OrderCreated",
                    occurred_at,
                    json.dumps(event),
                ),
            )

    return str(order_id)


@app.route("/orders", methods=["POST"])
def create_order():
    body = request.get_json(force=True, silent=False)
    customer_id = body.get("customer_id") if isinstance(body, dict) else None
    items = body.get("items", []) if isinstance(body, dict) else []

    if not customer_id:
        return jsonify({"error": "customer_id est requis"}), 400

    validation_error = validate_items(items)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        order_id = create_order_in_transaction(customer_id, items)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except psycopg.Error:
        app.logger.exception("Erreur PostgreSQL pendant la création de commande")
        return jsonify({"error": "Erreur PostgreSQL"}), 500

    return jsonify({"order_id": order_id, "status": "CREATED"}), 201


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    occurred_at = datetime.now(timezone.utc)
    event_id = uuid4()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orders
                    SET status = 'CANCELLED', version = version + 1, updated_at = %s
                    WHERE order_id = %s AND status = 'CREATED'
                    RETURNING customer_id, version
                    """,
                    (occurred_at, order_id),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
                    existing = cur.fetchone()
                    if existing is None:
                        return jsonify({"error": "Order not found"}), 404
                    return jsonify({"error": f"Commande déjà dans l'état {existing[0]}"}), 409

                customer_id, version = row
                event = {
                    "event_id": str(event_id),
                    "event_type": "OrderCancelled",
                    "occurred_at": occurred_at.isoformat(),
                    "aggregate_version": version,
                    "payload": {
                        "order_id": order_id,
                        "customer_id": customer_id,
                    },
                }

                cur.execute(
                    """
                    INSERT INTO outbox_events
                        (event_id, aggregate_id, aggregate_version, event_type, occurred_at, payload)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (event_id, order_id, version, "OrderCancelled", occurred_at, json.dumps(event)),
                )
    except psycopg.Error:
        app.logger.exception("Erreur PostgreSQL pendant l'annulation")
        return jsonify({"error": "Erreur PostgreSQL"}), 500

    return jsonify({"order_id": order_id, "status": "CANCELLED"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
