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
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]

fake = Faker("fr_FR")

# Reset pour un TP reproductible
products.drop()

categories = ["informatique", "mobilier", "papeterie", "electromenager", "jardin"]

documents = []
for _ in range(500):
    documents.append({
        "name": fake.catch_phrase(),
        "category": random.choice(categories),
        "price": round(random.uniform(5, 500), 2),
        "stock": random.randint(0, 200),
        "created_at": fake.date_time_this_year(),
    })

result = products.insert_many(documents)
print(f"{len(result.inserted_ids)} produits insérés.")

products.create_index("name")
products.create_index("price")
