# Explication détaillée du script : 22_validation_schema.py

Ce document détaille le code source du script Python illustrant la validation de documents à l'aide d'un schéma JSON dans MongoDB.

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et gestion des erreurs
```python
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
from pymongo.errors import WriteError

load_dotenv()
```
- Importe `MongoClient`, `load_dotenv`, les modules système, et l'exception `WriteError` pour intercepter les erreurs d'insertion liées à la validation.

### 2. Vérification et connexion à MongoDB
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

collection_name = "customers_validated"
```
- Valide la présence de l'URI, initialise le client MongoDB, sélectionne la base `training` et définit le nom de la collection.

### 3. Création de la collection avec validateur JSON Schema
```python
print(f"Suppression éventuelle de la collection {collection_name}...")
db[collection_name].drop()

print(f"Création de la collection {collection_name} validation JSON Schema...")

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
```
- Supprime la collection si elle existe, puis la recrée avec une règle de validation `$jsonSchema` imposant des types, des champs obligatoires (`required`), des expressions régulières (`pattern`), des énumérations (`enum`) et des bornes numériques (`minimum`/`maximum`).

### 4. Insertion d'un document valide
```python
print("
Insertion d'un document VALIDE...")
valid_doc = {
    "full_name": "Alice Dupont",
    "email": "alice.dupont@example.com",
    "segment": "gold",
    "age": 34,
}

customers_validated.insert_one(valid_doc)
print("Document valide inséré avec succès.")
```
- Insère un document respectant toutes les contraintes du schéma sans erreur.

### 5. Tentative d'insertion d'un document invalide
```python
print("
Tentative d'insertion d'un document INVALIDE...")
invalid_doc = {
    "full_name": "Bob Martin",
    "email": "bob.martin.example.com",  # pas de @
    "segment": "platinum",              # valeur non autorisée
    "age": 16,                          # trop jeune
}

try:
    customers_validated.insert_one(invalid_doc)
except WriteError as e:
    print("Echec d'insertion (validation de schéma) :")
    print(e.details)
```
- Tente d'insérer un document non conforme, intercepte l'exception `WriteError` levée par MongoDB et affiche les détails de l'échec.

### 6. Affichage du nombre de documents valides
```python
print(
    "
Nombre de documents valides dans la collection :",
    customers_validated.count_documents({}),
)
```
- Affiche le nombre total de documents valides présents dans la collection.
