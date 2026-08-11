from pymongo import MongoClient, ASCENDING, DESCENDING
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

products = MongoClient(MONGO_URI)["training"]["products"]

# 1. Produits dont le prix est compris entre 50 et 150 euros
q1 = products.find({"price": {"$gte": 50, "$lte": 150}})
print("Q1 - Plage de prix :", products.count_documents({"price": {"$gte": 50, "$lte": 150}}))

# 2. Produits dont le nom contient "solution" (insensible à la casse)
q2 = products.find({"name": {"$regex": "solution", "$options": "i"}})
print("Q2 - Regex sur nom :", products.count_documents({"name": {"$regex": "solution", "$options": "i"}}))

# 3. Les 10 produits les plus chers, triés par prix décroissant
q3 = products.find().sort("price", DESCENDING).limit(10)
print("Q3 - Top 10 prix décroissant :")
for p in q3:
    print(" -", p["name"], p["price"])

# 4. Pagination : page 3 avec 20 produits par page, triés par nom
#    (tri secondaire sur _id pour un ordre déterministe en cas de noms
#    identiques — sans ça, skip/limit n'est pas garanti stable)
page = 3
page_size = 20
q4 = (
    products.find()
    .sort([("name", ASCENDING), ("_id", ASCENDING)])
    .skip((page - 1) * page_size)
    .limit(page_size)
)
resultats_q4 = list(q4)
print(f"Q4 - Page {page} ({page_size} résultats/page), {len(resultats_q4)} trouvés :")
for p in resultats_q4:
    print(" -", p["name"], p["price"])

# 5. Produits en rupture de stock (stock = 0) d'une catégorie donnée, triés par prix croissant
q5 = products.find({"category": "informatique", "stock": 0}).sort("price", ASCENDING)
print("Q5 - Rupture stock informatique :", products.count_documents({"category": "informatique", "stock": 0}))
