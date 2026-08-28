# Explication détaillée du script : `13_ca_par_client_mois_sans_unwind.py`

Ce script calcule le chiffre d'affaires par client et par mois sur les commandes confirmées, mais présente la particularité d'avoir l'étape `$unwind` sur les items commentée (illustrant un cas particulier d'agrégation ou nécessitant une adaptation selon la structure).

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
- Initialisation standard et connexion à la collection `orders`.

---

## 2. Construction du pipeline d'agrégation

```python
pipeline = [
    {"$match": {"status": "CONFIRMED"}},
    # {"$unwind": "$items"},
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
- `# {"$unwind": "$items"}` : **Étape commentée** dans ce script.
- `{"$group": {...}}` : Regroupement par client, année et mois avec calcul du CA.
- `{"$lookup": {...}}` et `{"$unwind": "$customer"}` : Jointure avec la collection `customers`.
- `{"$project": {...}}` et `{"$sort": {...}}` : Projection et tri des résultats.

---

## 3. Exécution et affichage

```python
results = list(orders.aggregate(pipeline))

if not results:
    print(
        "Aucun résultat : vérifiez que des commandes CONFIRMED existent "
        "dans la collection orders."
    )
else:
    print(f"Nombre de lignes de CA client/mois : {len(results)}")
    print("\nAperçu des 20 premières lignes :\n")
    for doc in results[:20]:
        print(
            f"{doc['year']}-{doc['month']:02d} | "
            f"{doc['customer_name']} | CA = {doc['revenue']:.2f} €"
        )
```
- Exécute le pipeline et affiche l'aperçu des 20 premières lignes.
