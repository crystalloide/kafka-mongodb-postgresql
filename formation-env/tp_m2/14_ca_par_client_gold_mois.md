# Explication détaillée du script : `14_ca_par_client_gold_mois.py`

Ce script filtre le chiffre d'affaires par client et par mois en se restreignant exclusivement aux clients appartenant au segment `"gold"`.

---

## 1. Importations et connexion

```python
from pymongo import MongoClient
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

orders = db["orders"]
```
- Initialisation de la connexion MongoDB.

---

## 2. Construction du pipeline d'agrégation (segment gold)

```python
pipeline = [
    {"$match": {"status": "CONFIRMED"}},
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": {
                "customer_id": "$customer_id",
                "year": {"$year": "$order_date"},
                "month": {"$month": "$order_date"},
            },
            "revenue": {
                "$sum": {
                    "$multiply": ["$items.unit_price", "$items.quantity"]
                }
            },
        }
    },
    {
        "$lookup": {
            "from": "customers",
            "localField": "_id.customer_id",
            "foreignField": "_id",
            "as": "customer",
        }
    },
    {"$unwind": "$customer"},
    {"$match": {"customer.segment": "gold"}},  # <-- nouvelle étape
    {
        "$project": {
            "_id": 0,
            "customer_id": "$_id.customer_id",
            "customer_name": "$customer.full_name",
            "year": "$_id.year",
            "month": "$_id.month",
            "revenue": 1,
        }
    },
    {"$sort": {"year": 1, "month": 1, "customer_name": 1}},
]
```
- `{"$match": {"status": "CONFIRMED"}}` : Filtre les commandes confirmées.
- `{"$unwind": "$items"}` : Décompose les articles.
- `{"$group": {...}}` : Groupe par client et par mois/année pour sommer le CA.
- `{"$lookup": {...}}` et `{"$unwind": "$customer"}` : Jointure avec la collection `customers`.
- `{"$match": {"customer.segment": "gold"}}` : Filtre post-jointure ne conservant que les clients gold.
- `{"$project": {...}}` et `{"$sort": {...}}` : Formatage et tri chronologique/alphabétique.

---

## 3. Exécution et affichage

```python
results = list(orders.aggregate(pipeline))

if not results:
    print("Aucun résultat : vérifiez qu'il existe des clients de segment 'gold' avec des commandes CONFIRMED.")
else:
    print(f"Nombre de lignes de CA client/mois (segment gold) : {len(results)}")
    print("\nAperçu des 20 premières lignes :\n")
    for doc in results[:20]:
        print(
            f"{doc['year']}-{doc['month']:02d} | "
            f"{doc['customer_name']} | CA = {doc['revenue']:.2f} €"
        )
```
- Exécute le pipeline et affiche les résultats spécifiques au segment gold.
