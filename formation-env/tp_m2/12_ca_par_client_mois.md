# Explication détaillée du script : `12_ca_par_client_mois.py`

Ce script utilise le framework d'agrégation de MongoDB (`aggregate`) pour calculer le chiffre d'affaires (CA) réalisé par client et par mois, uniquement sur les commandes confirmées, en effectuant une jointure avec la collection des clients.

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
- Importations habituelles, chargement de l'environnement, vérification de l'URI et sélection de la collection `orders`.

---

## 2. Construction du pipeline d'agrégation

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
- `{"$match": {"status": "CONFIRMED"}}` : Filtre les documents pour ne conserver que les commandes dont le statut est `"CONFIRMED"`.
- `{"$unwind": "$items"}` : Décompose le tableau des articles pour traiter chaque article individuellement.
- `{"$group": {...}}` : Groupe les résultats par `customer_id`, `year` (extrait de `order_date`) et `month` (extrait de `order_date`). Calcule le chiffre d'affaires (`revenue`) en sommant le produit de la quantité par le prix unitaire.
- `{"$lookup": {...}}` : Effectue une jointure (`left outer join`) avec la collection `customers` en reliant `_id.customer_id` de la table orders au champ `_id` de la collection customers. Les résultats sont stockés dans un tableau temporaire `customer`.
- `{"$unwind": "$customer"}` : Transforme le tableau `customer` (résultant du `$lookup`) en un objet unique pour faciliter l'accès aux champs du client.
- `{"$project": {...}}` : Restructure le document final pour afficher proprement les champs voulus (`customer_id`, `customer_name`, `year`, `month`, `revenue`) tout en masquant l'identifiant technique `_id`.
- `{"$sort": {...}}` : Trie les résultats par ordre croissant sur l'année, le mois, puis le nom du client.

---

## 3. Exécution et affichage des résultats

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
- `orders.aggregate(pipeline)` : Exécute le pipeline d'agrégation et convertit le curseur en liste Python.
- Vérifie si des résultats sont retournés et affiche un aperçu formaté des 20 premières lignes.
