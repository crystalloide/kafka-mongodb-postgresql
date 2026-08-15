from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import sys
import random
import time

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier du projet et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
orders_cs = db["orders_cs"]

fake = Faker("fr_FR")

print("Reset de la collection training.orders_cs...")
orders_cs.drop()

print("Insertion de commandes initiales...")
order_ids = []
for i in range(10):
    doc = {
        "order_ref": f"CMD-{1000 + i}",
        "customer_name": fake.name(),
        "status": random.choice(["NEW", "PROCESSING", "COMPLETED"]),
        "amount": round(random.uniform(50, 500), 2),
    }
    result = orders_cs.insert_one(doc)
    order_ids.append(result.inserted_id)

print(f"{len(order_ids)} commandes insérées.\n")

print("Boucle de production : insert + update toutes les 2 secondes.")
print("Appuyez sur Ctrl+C pour arrêter.\n")

try:
    while True:
        # INSERT d'une nouvelle commande
        doc = {
            "order_ref": f"CMD-{random.randint(2000, 9999)}",
            "customer_name": fake.name(),
            "status": "NEW",
            "amount": round(random.uniform(50, 500), 2),
        }
        result = orders_cs.insert_one(doc)
        print(f"[INSERT] Nouvelle commande {doc['order_ref']} (id={result.inserted_id})")

        # UPDATE sur une commande existante
        if order_ids:
            target_id = random.choice(order_ids)
            new_status = random.choice(["PROCESSING", "COMPLETED", "CANCELLED"])
            new_amount = round(random.uniform(50, 500), 2)
            orders_cs.update_one(
                {"_id": target_id},
                {
                    "$set": {
                        "status": new_status,
                        "amount": new_amount,
                    }
                },
            )
            print(
                f"[UPDATE] Commande id={target_id} -> "
                f"status={new_status}, amount={new_amount}"
            )

        time.sleep(2)
except KeyboardInterrupt:
    print("\nArrêt du producteur.")