from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os
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
products = db["products"]

print("Nombre de documents dans products :", products.count_documents({}))

# Requête cible
query = {"category": "informatique", "price": {"$gte": 50, "$lte": 150}}

print("\nPlan d'exécution AVANT création d'index :")
explain_before = products.find(query).explain()
print("winningPlan.stage =", explain_before["queryPlanner"]["winningPlan"]["stage"])

# Index simple sur price
print("\nCréation d'un index simple sur 'price'...")
products.create_index("price")

print("Plan d'exécution APRES index simple sur price :")
explain_after_price = products.find(query).explain()
print("winningPlan.stage =", explain_after_price["queryPlanner"]["winningPlan"]["stage"])

# Index composé sur (category, price)
print("\nCréation d'un index composé sur ('category', 'price')...")
products.create_index([("category", ASCENDING), ("price", ASCENDING)])

print("Plan d'exécution APRES index composé (category, price) :")
explain_after_compound = products.find(query).explain()
print("winningPlan.stage =", explain_after_compound["queryPlanner"]["winningPlan"]["stage"])

# Variante avec executionStats
print("\nPlan d'exécution avec executionStats, APRES index composé :")
explain_stats = products.find(query).explain("executionStats")
print("nReturned      =", explain_stats["executionStats"]["nReturned"])
print("totalDocsExamined =", explain_stats["executionStats"]["totalDocsExamined"])

print("\nListe des index de la collection products :")
for idx in products.list_indexes():
    print(idx)