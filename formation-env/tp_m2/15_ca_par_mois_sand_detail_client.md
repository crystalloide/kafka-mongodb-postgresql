# Explication détaillée du script : `15_ca_par_mois_sand_detail_client.py`

Ce script calcule le chiffre d'affaires global agrégé par mois (sans détail par client), basé sur les commandes confirmées.

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
- Initialisation et connexion à la base de données.

---

## 2. Construction du pipeline d'agrégation par mois

```python
pipeline = [
    {"$match": {"status": "CONFIRMED"}},
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": {
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
        "$project": {
            "_id": 0,
            "year": "$_id.year",
            "month": "$_id.month",
            "revenue": 1,
        }
    },
    {"$sort": {"year": 1, "month": 1}},
]
```
- `{"$match": {"status": "CONFIRMED"}}` : Conserve les commandes confirmées.
- `{"$unwind": "$items"}` : Décompose les articles.
- `{"$group": {...}}` : Groupe uniquement par année et mois, en calculant le CA total (`revenue`).
- `{"$project": {...}}` et `{"$sort": {...}}` : Projection des champs et tri chronologique.

---

## 3. Exécution et affichage

```python
results = list(orders.aggregate(pipeline))

if not results:
    print("Aucun résultat : vérifiez que des commandes CONFIRMED existent dans la collection orders.")
else:
    print(f"Nombre de mois avec du CA : {len(results)}")
    print("\nCA par mois :\n")
    for doc in results:
        print(f"{doc['year']}-{doc['month']:02d} | CA = {doc['revenue']:.2f} €")
```
- Exécute l'agrégation et affiche le CA global pour chaque mois.
