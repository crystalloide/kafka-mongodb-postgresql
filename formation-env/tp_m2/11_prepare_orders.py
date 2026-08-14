from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import random
import sys

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier du projet et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]

customers = db["customers"]
orders = db["orders"]

fake = Faker("fr_FR")

# Reset pour un TP reproductible
print("Suppression des collections customers et orders si elles existent déjà...")
customers.drop()
orders.drop()

# Génération de ~50 clients
print("Insertion des clients...")
customer_ids = []
for _ in range(50):
    doc = {
        "full_name": fake.name(),
        "email": fake.email(),
        "segment": random.choice(["bronze", "silver", "gold"]),
    }
    result = customers.insert_one(doc)
    customer_ids.append(result.inserted_id)

print(f"{len(customer_ids)} clients insérés.")

# Génération de ~300 commandes avec items embarqués
print("Insertion des commandes...")
statuses = ["CONFIRMED", "PENDING", "CANCELLED"]

order_count = 0
for _ in range(300):
    customer_id = random.choice(customer_ids)
    nb_items = random.randint(1, 5)
    items = []
    for _ in range(nb_items):
        unit_price = round(random.uniform(10, 300), 2)
        quantity = random.randint(1, 5)
        items.append(
            {
                "product_name": fake.catch_phrase(),
                "unit_price": unit_price,
                "quantity": quantity,
            }
        )

    order = {
        "customer_id": customer_id,
        "order_date": fake.date_time_this_year(),
        "status": random.choice(statuses),
        "items": items,
    }

    orders.insert_one(order)
    order_count += 1

print(f"{order_count} commandes insérées.")
print("Jeu de données customers/orders prêt pour les agrégations.")