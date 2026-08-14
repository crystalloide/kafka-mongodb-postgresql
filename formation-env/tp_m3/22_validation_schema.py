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

# Document VALIDE
print("\nInsertion d'un document VALIDE...")
valid_doc = {
    "full_name": "Alice Dupont",
    "email": "alice.dupont@example.com",
    "segment": "gold",
    "age": 34,
}

customers_validated.insert_one(valid_doc)
print("Document valide inséré avec succès.")

# Document INVALIDE
print("\nTentative d'insertion d'un document INVALIDE...")
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

print(
    "\nNombre de documents valides dans la collection :",
    customers_validated.count_documents({}),
)