# Explication détaillée du script : 23_optimisation_requete_lente.py

Ce document détaille le code source du script Python illustrant l'optimisation d'une requête complexe à l'aide de la règle ESR (Equality, Sort, Range).

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os
import sys

load_dotenv()
```
- Importe les modules nécessaires (`MongoClient`, `ASCENDING`, `load_dotenv`, `os`, `sys`) et charge l'environnement.

### 2. Récupération et validation de l'URI MongoDB
```python
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier du projet et qu'il contient bien :
"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]
```
- Récupère l'URI, vérifie sa validité, et initialise la connexion à la collection `products` de la base `training`.

### 3. Définition de la requête métier complexe
```python
query = {
    "category": "informatique",
    "stock": {"$lte": 20},
    "price": {"$gte": 50, "$lte": 300},
}
```
- Définit une requête combinant un filtre d'égalité (`category`), un filtre d'intervalle sur le stock (`stock`) et un filtre d'intervalle sur le prix (`price`).

### 4. Réinitialisation des index
```python
print("Reset des index de products (on garde uniquement _id_)...")
for idx in products.list_indexes():
    name = idx["name"]
    if name != "_id_":
        print(f" - drop_index('{name}')")
        products.drop_index(name)
```
- Supprime tous les index secondaires de la collection pour garantir un test initial sans index adapté.

### 5. Fonction d'analyse détaillée (`describe_plan`)
```python
def describe_plan(plan, label):
    qp = plan.get("queryPlanner", {})
    wp = qp.get("winningPlan", {})
    es = plan.get("executionStats", {})

    stage = wp.get("stage")
    input_stage = wp.get("inputStage", {})
    input_stage_name = input_stage.get("stage")
    index_name = input_stage.get("indexName")

    print(f"
=== {label} ===")
    print("winningPlan.stage       :", stage)
    if input_stage_name:
        print("winningPlan.inputStage  :", input_stage_name)
    if index_name:
        print("indexName               :", index_name)

    if es:
        print("nReturned               :", es.get("nReturned"))
        print("totalDocsExamined       :", es.get("totalDocsExamined"))
        print("totalKeysExamined       :", es.get("totalKeysExamined"))
        print("executionTimeMillis     :", es.get("executionTimeMillis"))
```
- Fonction permettant d'afficher le plan gagnant, les étapes d'exécution et les statistiques détaillées (`executionStats`).

### 6. Analyse AVANT index adapté
```python
explain_before = products.find(query).explain()
describe_plan(explain_before, "AVANT index adapté")
```
- Exécute l'explication de la requête sans index adapté (résultat attendu : `COLLSCAN`).

### 7. Création de l'index composé selon la règle ESR
```python
print("
Création de l'index adapté à CETTE requête précise :
")
print("
Requête : ",query,"
")
print("
Règle ESR (Equality, Sort, Range) : "category" est un filtre d'égalité (E), il passe en premier.
")
print("
Les critères "stock" et "price" sont des filtres d'intervalle (R), ils viennent ensuite :
")

print("
Création de l'index composé (category, stock, price)...")
products.create_index([
    ("category", ASCENDING),
    ("stock", ASCENDING),
    ("price", ASCENDING),
])
```
- Crée l'index composé en appliquant rigoureusement la **règle ESR** (Equality pour `category`, Range pour `stock` et `price`).

### 8. Analyse APRES index adapté
```python
explain_after = products.find(query).explain()
describe_plan(explain_after, "APRES index adapté (category, stock, price)")
```
- Analyse à nouveau la requête après la création de l'index (résultat attendu : `IXSCAN` et performance optimisée).

### 9. Affichage final des index
```python
print("
Index finaux de la collection products :")
for idx in products.list_indexes():
    print(idx)
```
- Affiche l'état final des index de la collection.
