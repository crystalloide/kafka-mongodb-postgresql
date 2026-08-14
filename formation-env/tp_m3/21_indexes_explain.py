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

query = {"category": "informatique", "price": {"$gte": 50, "$lte": 150}}

print("Nombre de documents dans products :", products.count_documents({}))

# Reset des index (on garde uniquement _id_)
print("\nReset des index de products (on garde uniquement _id_)...")
for idx in products.list_indexes():
    name = idx["name"]
    if name != "_id_":
        print(f" - drop_index('{name}')")
        products.drop_index(name)

print("\nIndex après reset :")
for idx in products.list_indexes():
    print(idx)


def describe_plan(plan, label):
    qp = plan.get("queryPlanner", {})
    wp = qp.get("winningPlan", {})
    es = plan.get("executionStats", {})

    stage = wp.get("stage")
    input_stage = wp.get("inputStage", {})
    input_stage_name = input_stage.get("stage")
    index_name = input_stage.get("indexName")

    print(f"\n=== {label} ===")
    print("winningPlan.stage       :", stage)
    if input_stage_name:
        print("winningPlan.inputStage  :", input_stage_name)
    if index_name:
        print("indexName               :", index_name)

    if es:
        print("nReturned               :", es.get("nReturned"))
        print("totalDocsExamined       :", es.get("totalDocsExamined"))
        print("totalKeysExamined       :", es.get("totalKeysExamined"))


# 1. Plan AVANT tout index (hors _id_)
explain_before = products.find(query).explain()
describe_plan(explain_before, "AVANT index spécifique")


# 2. Création d'un index simple sur price
print("\nCréation d'un index simple sur 'price'...")
products.create_index("price")

explain_after_price = products.find(query).explain()
describe_plan(explain_after_price, "APRES index simple sur price")


# 3. Création d'un index composé sur (category, price)
print("\nCréation d'un index composé sur ('category', 'price')...")
products.create_index([("category", ASCENDING), ("price", ASCENDING)])

explain_after_compound = products.find(query).explain()
describe_plan(explain_after_compound, "APRES index composé (category, price)")


print("\nIndex finaux de la collection products :")
for idx in products.list_indexes():
    print(idx)