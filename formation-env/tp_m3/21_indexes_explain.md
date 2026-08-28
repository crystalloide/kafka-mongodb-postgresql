# Explication détaillée du script : 21_indexes_explain.py

Ce document détaille le code source du script Python permettant de comparer l'efficacité d'un index simple par rapport à un index composé sur MongoDB.

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
- `from pymongo import MongoClient, ASCENDING`: Importe le client MongoDB et la constante de tri `ASCENDING`.
- `from dotenv import load_dotenv`: Importe la fonction pour charger les variables d'environnement depuis un fichier `.env`.
- `import os`, `import sys`: Importe les modules système et d'interaction avec le système d'exploitation.
- `load_dotenv()`: Charge les variables d'environnement.

### 2. Récupération et vérification de l'URI MongoDB
```python
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier du projet et qu'il contient bien :
"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )
```
- Récupère la variable `MONGO_URI` et quitte le script avec un message d'erreur si elle est absente.

### 3. Connexion à la base de données et à la collection
```python
client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]
```
- Établit la connexion avec le client MongoDB, sélectionne la base de données `training` et la collection `products`.

### 4. Définition de la requête et comptage initial
```python
query = {"category": "informatique", "price": {"$gte": 50, "$lte": 150}}

print("Nombre de documents dans products :", products.count_documents({}))
```
- Définit une requête filtrant les produits informatiques dont le prix est entre 50 et 150.
- Affiche le nombre total de documents dans la collection.

### 5. Réinitialisation des index
```python
print("
Reset des index de products (on garde uniquement _id_)...")
for idx in products.list_indexes():
    name = idx["name"]
    if name != "_id_":
        print(f" - drop_index('{name}')")
        products.drop_index(name)

print("
Index après reset :")
for idx in products.list_indexes():
    print(idx)
```
- Parcourt tous les index et supprime ceux différents de `_id_` pour repartir d'une base propre.

### 6. Fonction d'analyse du plan d'exécution (`describe_plan`)
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
```
- Fonction utilitaire pour extraire et afficher les métriques clés du plan d'exécution (`winningPlan`, `stage`, `executionStats`).

### 7. Étape 1 : Plan AVANT tout index spécifique
```python
explain_before = products.find(query).explain()
describe_plan(explain_before, "AVANT index spécifique")
```
- Exécute `.explain()` sans index spécifique, provoquant un balayage complet (`COLLSCAN`).

### 8. Étape 2 : Création d'un index simple sur `price`
```python
print("
Création d'un index simple sur 'price'...")
products.create_index("price")

explain_after_price = products.find(query).explain()
describe_plan(explain_after_price, "APRES index simple sur price")
```
- Crée un index simple sur `price` et analyse l'impact sur le plan d'exécution.

### 9. Étape 3 : Création d'un index composé sur `(category, price)`
```python
print("
Création d'un index composé sur ('category', 'price')...")
products.create_index([("category", ASCENDING), ("price", ASCENDING)])

explain_after_compound = products.find(query).explain()
describe_plan(explain_after_compound, "APRES index composé (category, price)")
```
- Crée un index composé combinant `category` et `price`, optimisant pleinement la recherche.

### 10. Affichage final des index
```python
print("
Index finaux de la collection products :")
for idx in products.list_indexes():
    print(idx)
```
- Affiche la liste finale des index présents sur la collection.
