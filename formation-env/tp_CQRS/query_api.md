# Explication détaillée du script : query_api.py 

Ce document détaille le code source du script Python implémentant l'**API de Lecture (Query API)** basée sur Flask . Elle expose des endpoints REST permettant de consulter la vue matérialisée MongoDB (`orders_view`) alimentée par le projecteur CQRS .

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et initialisation de Flask
```python
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
```
- Charge l'environnement, initialise la connexion MongoDB sur la collection `orders_view` et instancie l'application Flask (`app`) .

### 2. Endpoint de consultation d'une commande par son ID
```python
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    doc = orders_view.find_one({"order_id": order_id}, {"_id": 0})
    if not doc:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(doc)
```
- Route GET `/orders/<order_id>` : Recherche un document dans `orders_view` correspondant à l'identifiant de commande fourni en excluant l'ID MongoDB par défaut (`{"_id": 0}`) . Précision : ``_id`` n'est pas supprimé de MongoDB : il est seulement exclu du résultat de cette requête grâce à la projection MongoDB.
- Renvoie une erreur 404 si la commande n'existe pas, ou le document JSON le cas échéant .

### 3. Endpoint de consultation des commandes d'un client
```python
@app.route("/customers/<customer_id>/orders", methods=["GET"])
def get_customer_orders(customer_id: str):
    docs = list(orders_view.find({"customer_id": customer_id}, {"_id": 0}))
    return jsonify(docs)
```
- Route GET `/customers/<customer_id>/orders` : Récupère sous forme de liste toutes les commandes associées à un client donné (`customer_id`) dans la vue matérialisée, sans l'attribut `_id` .

### 4. Lancement de l'application Flask
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```
- Démarre le serveur web Flask sur le port `5001` en mode debug .
- Flask get_json(force=True) :  Il n'y a pas de problème ici, puisque query_api.py ne reçoit pas de JSON. Dans ``command_api.py``, en revanche, **request.get_json(force=True)** signifie que Flask tente de parser la requête comme JSON même si le Content-Type n'indique pas **application/json**. Flask documente explicitement ce comportement.
