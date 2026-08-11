from pymongo import MongoClient
from dotenv import load_dotenv
import os
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

# --- CREATE ---
print("Create : ajout d'un seul produit : insert_one")
produit = {
    "name": "Clavier mecanique",
    "category": "informatique",
    "price": 79.90,
    "stock": 25,
}
result = products.insert_one(produit)
print("Inséré avec _id :", result.inserted_id)

print("Create : ajout de plusieurs produits : insert_many")
produits_liste = [
    {"name": "Souris sans fil", "category": "informatique", "price": 29.90, "stock": 100},
    {"name": "Ecran 27 pouces", "category": "informatique", "price": 199.00, "stock": 15},
    {"name": "Chaise de bureau", "category": "mobilier", "price": 149.50, "stock": 8},
]
result = products.insert_many(produits_liste)
print("IDs insérés :", result.inserted_ids)

# --- READ ---
print("Read : lecture d'un seul produit : find_one")
un_produit = products.find_one({"category": "mobilier"})
print("Un produit mobilier :", un_produit)

print("Read : lecture de plusieurs produits : find")
for p in products.find({"category": "informatique"}):
    print(p["name"], p["price"])

# --- UPDATE ---
print("Update : mise à jour d'un seul produit : update_one")
products.update_one(
    {"name": "Clavier mecanique"},
    {"$set": {"price": 69.90}}
)

print("Update : mise à jour de plusieurs produits : update_many")
products.update_many(
    {"category": "informatique"},
    {"$inc": {"stock": -1}}
)

# --- DELETE ---
print("Delete : suppression de plusieurs produits : delete_many")
products.delete_many({"category": "mobilier"})

print("Nombre de produits restants :", products.count_documents({}))
