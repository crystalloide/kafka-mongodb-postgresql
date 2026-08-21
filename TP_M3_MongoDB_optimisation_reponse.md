## 4. Exercice guidé — Optimiser une requête lente (corrigé)

Objectif : faire vivre aux stagiaires le cycle complet **diagnostic → correction → vérification**, sur une requête "métier" réaliste (produits d'une catégorie, en stock faible, dans une fourchette de prix).

Créez le fichier `23_optimisation_requete_lente.py` :

```python
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

# Requête "métier" volontairement lente : produits d'une catégorie,
# en stock faible, dans une fourchette de prix -> 3 champs combinés
query = {
    "category": "informatique",
    "stock": {"$lte": 20},
    "price": {"$gte": 50, "$lte": 300},
}

# On repart d'une base propre (comme dans le script 21) pour que la
# démonstration AVANT/APRES soit fiable, quel que soit l'ordre dans
# lequel les scripts précédents ont été exécutés.
print("Reset des index de products (on garde uniquement _id_)...")
for idx in products.list_indexes():
    name = idx["name"]
    if name != "_id_":
        print(f" - drop_index('{name}')")
        products.drop_index(name)


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
        print("executionTimeMillis     :", es.get("executionTimeMillis"))

print("\nRequête : ",query,"\n")

# 1. AVANT : aucun index adapté -> COLLSCAN attendu
# NB : Cursor.explain() (pymongo) ne prend pas d'argument de verbosité
# comme dans mongosh — il s'exécute en "allPlansExecution", qui inclut
# déjà les executionStats.
explain_before = products.find(query).explain()
describe_plan(explain_before, "AVANT index adapté")

# 2. Création de l'index adapté à CETTE requête précise.
#    Règle ESR (Equality, Sort, Range) : "category" est un filtre
#    d'égalité (E), il passe en premier ; "stock" et "price" sont des
#    filtres d'intervalle (R), ils viennent ensuite.
print("\nCréation de l'index composé (category, stock, price)...")
products.create_index([
    ("category", ASCENDING),
    ("stock", ASCENDING),
    ("price", ASCENDING),
])

# 3. APRES : l'index doit être utilisé -> IXSCAN attendu
explain_after = products.find(query).explain()
describe_plan(explain_after, "APRES index adapté (category, stock, price)")

print("\nIndex finaux de la collection products :")
for idx in products.list_indexes():
    print(idx)
```

Exécutez le script :

```bash
python 23_optimisation_requete_lente.py
```

### Points pédagogiques à commenter

- **Avant** : `winningPlan.stage` = `COLLSCAN`, `totalDocsExamined` ≈ nombre total de documents de `products` (~500), quel que soit le nombre de résultats réellement pertinents (`nReturned`).
- **Après** : `winningPlan.stage` = `IXSCAN` sur l'index `category_1_stock_1_price_1`, et `totalDocsExamined` se rapproche fortement de `totalKeysExamined` et de `nReturned` — signe que l'index élimine efficacement les documents non pertinents avant même de les charger.
- Insister sur la **règle ESR** (Equality → Sort → Range) pour l'ordre des champs dans un index composé : un champ d'égalité placé en tête permet à MongoDB de "sauter" directement aux bonnes clés d'index, alors qu'un champ d'intervalle placé trop tôt limite l'efficacité du reste de l'index.
- Variante à proposer aux plus rapides : comparer avec un index `(category, stock)` seul (sans `price`) et observer que `price` est alors filtré en mémoire après le `FETCH` — bon moyen de montrer qu'un `IXSCAN` n'est pas toujours pleinement optimal, et qu'il faut regarder `totalDocsExamined` vs `nReturned`, pas seulement le nom du stage.
- Rappeler le compromis : chaque index accélère les lectures mais a un coût à l'écriture (insert/update) et en espace disque — un index composé "sur mesure" pour une requête récurrente est un choix raisonné, pas un réflexe systématique.
