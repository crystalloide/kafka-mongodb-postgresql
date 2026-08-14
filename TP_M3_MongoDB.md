## TP M3 — Index, performance et validation de schéma

**Durée** : 45 min

**Prérequis** :
- TP M1 et TP M2 réalisés (base `training` créée, collections `products`, `customers`, `orders` existantes).
- MongoDB 7.0.7 démarré (Docker Compose).
- venv activé.
- `pymongo>=4.7,<5`, `faker`, `python-dotenv` installés (`requirements.txt`).
- fichier `.env` avec `MONGO_URI` configuré (même valeur que pour les TP précédents).

## Objectifs

- Comprendre l'impact des **index** sur les performances de requêtes.
- Savoir utiliser `explain()` pour distinguer `COLLSCAN` (scan complet de collection) et `IXSCAN` (scan via index).
- Mettre en place un **schéma de validation** JSON Schema (`$jsonSchema`) sur une collection pour améliorer la qualité/gouvernance des données.
- Optimiser une requête lente en ajoutant l'index adéquat et mesurer le gain avec `explain("executionStats")`.

---

## On se positionne dans le répertoire du TP : 

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_m3
ls
```

## 1. Rappel sur les index et `explain()` (10 min)

Un index dans MongoDB est une structure de données qui permet de rechercher rapidement des documents selon la valeur d'un ou plusieurs champs.

Sans index adapté, MongoDB doit parcourir **tous les documents** d'une collection (plan `COLLSCAN`) pour trouver les résultats.

Avec un index, MongoDB peut utiliser un plan `IXSCAN` (scan d'index) beaucoup plus efficace, surtout sur des volumes importants.

`explain()` permet d'inspecter le plan de requête choisi par MongoDB :
- `winningPlan.stage` = `COLLSCAN` → scan complet.
- `winningPlan.stage` = `IXSCAN` → utilisation d'un index.

---

## 2. Script 21_indexes_explain.py — Index simples, composés et `explain()` (20 min)

Objectif :
- Créer un index simple sur `price` et un index composé sur `(category, price)` dans la collection `products`.
- Utiliser `explain()` pour observer la différence de plan d'exécution sur une requête filtrant par `price` et `category`.

Créez le fichier `21_indexes_explain.py` :

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

print("Nombre de documents dans products :", products.count_documents({}))

# 1. Requête sans index dédié
query = {"category": "informatique", "price": {"$gte": 50, "$lte": 150}}

print("\nPlan d'exécution AVANT création d'index :")
explain_before = products.find(query).explain()
print(explain_before["queryPlanner"]["winningPlan"]["stage"])

# 2. Création d'un index simple sur price
print("\nCréation d'un index simple sur 'price'...")
products.create_index("price")

print("Plan d'exécution APRES index simple sur price :")
explain_after_price = products.find(query).explain()
print(explain_after_price["queryPlanner"]["winningPlan"]["stage"])

# 3. Création d'un index composé sur (category, price)
print("\nCréation d'un index composé sur ('category', 'price')...")
products.create_index([("category", ASCENDING), ("price", ASCENDING)])

print("Plan d'exécution APRES index composé (category, price) :")
explain_after_compound = products.find(query).explain()
print(explain_after_compound["queryPlanner"]["winningPlan"]["stage"])

# Optionnel : afficher le nombre d'index
print("\nListe des index de la collection products :")
for idx in products.list_indexes():
    print(idx)
```

Exécutez le script :

```bash
python 21_indexes_explain.py
```

### Points pédagogiques à commenter

- Sur un jeu de données `products` (≈500 documents, créé dans le TP M1), la différence de temps ne sera pas énorme mais `winningPlan.stage` basculera de `COLLSCAN` vers `IXSCAN`.
- L'index simple sur `price` peut être utilisé, mais l'index composé `(category, price)` est plus adapté aux requêtes où les deux champs sont filtrés.
- On peut utiliser `explain("executionStats")` pour comparer des métriques comme `nReturned` (nombre de documents renvoyés) et `totalDocsExamined` (documents examinés).

---

## 3. Script 22_validation_schema.py — Validation JSON Schema (15 min)

Objectif : ajouter une **validation de schéma** sur une collection `customers_validated` pour contrôler la qualité des données.

La validation de schéma se fait via l'option `validator` lors de la création de la collection, avec une clause `$jsonSchema` qui décrit la forme attendue des documents.

Créez le fichier `22_validation_schema.py` :

```python
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
from pymongo.errors import WriteError

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

# On crée une nouvelle collection dédiée à la validation
collection_name = "customers_validated"

print(f"Suppression éventuelle de la collection {collection_name}...")
db[collection_name].drop()

print(f"Création de la collection {collection_name} avec validation JSON Schema...")

db.create_collection(
    collection_name,
    validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["full_name", "email", "segment"],
            "properties": {
                "full_name": {
                    "bsonType": "string",
                    "description": "Nom complet du client (obligatoire)",
                },
                "email": {
                    "bsonType": "string",
                    "pattern": "^.+@.+$",
                    "description": "Adresse email au format simple (obligatoire)",
                },
                "segment": {
                    "enum": ["bronze", "silver", "gold"],
                    "description": "Segment client parmi bronze/silver/gold (obligatoire)",
                },
                "age": {
                    "bsonType": "int",
                    "minimum": 18,
                    "maximum": 120,
                    "description": "Age du client (optionnel, entre 18 et 120)",
                },
            },
            "additionalProperties": True,
        }
    },
)

customers_validated = db[collection_name]

# 1. Document VALIDE
print("\nInsertion d'un document VALIDE...")
valid_doc = {
    "full_name": "Alice Dupont",
    "email": "alice.dupont@example.com",
    "segment": "gold",
    "age": 34,
}

customers_validated.insert_one(valid_doc)
print("Document valide inséré avec succès.")

# 2. Document INVALIDE (email sans @, segment inconnu, age < 18)
print("\nTentative d'insertion d'un document INVALIDE...")
invalid_doc = {
    "full_name": "Bob Martin",
    "email": "bob.martin.example.com",  # pas de @
    "segment": "platinum",  # valeur non autorisée
    "age": 16,  # trop jeune
}

try:
    customers_validated.insert_one(invalid_doc)
except WriteError as e:
    print("Echec d'insertion (validation de schéma) :")
    print(e.details)

print("\nNombre de documents valides dans la collection :", customers_validated.count_documents({}))
```

Exécutez le script :

```bash
python 22_validation_schema.py
```

### Points pédagogiques à commenter

- La validation JSON Schema est une brique de **gouvernance des données** : elle empêche l'insertion de documents non conformes (par exemple des segments inconnus, des emails invalides, des âges incohérents).
- Les messages d'erreur de `WriteError` contiennent le détail des violations (utile pour le debugging et pour les TP sur la qualité de données).
- La validation ne corrige pas les données existantes : elle s'applique aux insert/update futurs.

---

## 4. Exercice guidé — Optimiser une requête lente (option, 5–10 min)

Proposez aux stagiaires de :

1. Écrire une requête volontairement "lente" sur `products`, par exemple :
   - Filtrer sur une combinaison de champs non indexés (ex. `category`, `stock`, `price`).
2. Observer le plan via `explain("executionStats")` :
   - `totalDocsExamined` élevé, plan `COLLSCAN`.
3. Créer l'index adapté (par exemple `(category, stock)` ou `(category, price)`).
4. Relancer la même requête avec `explain("executionStats")` pour constater la baisse de `totalDocsExamined` et le passage à `IXSCAN`.

Cela conclut le TP M3 en développant le réflexe : **diagnostiquer une requête lente et choisir l'index approprié**.
