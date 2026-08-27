import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["training"]
orders_view = db["orders_view"]

app = Flask(__name__)

@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    doc = orders_view.find_one({"order_id": order_id}, {"_id": 0})
    if not doc:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(doc)

@app.route("/customers/<customer_id>/orders", methods=["GET"])
def get_customer_orders(customer_id: str):
    docs = list(orders_view.find({"customer_id": customer_id}, {"_id": 0}))
    return jsonify(docs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)