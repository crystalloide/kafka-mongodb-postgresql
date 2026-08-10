from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://formation:formation@localhost:27017/?authSource=admin",
)

client = MongoClient(MONGO_URI)

# Vérifier que le serveur répond ET que l'authentification est valide
try:
    print(client.admin.command("ping"))
except ServerSelectionTimeoutError:
    print("Connexion impossible : vérifiez host/port dans MONGO_URI.")
    raise
except OperationFailure:
    print("Authentification refusée : vérifiez user/password/authSource dans MONGO_URI.")
    raise

# Lister les bases existantes
print("Bases disponibles :", client.list_database_names())

# Créer/obtenir la base "training" (elle n'existe réellement
# qu'après la première écriture dans une collection)
db = client["training"]
print("Base sélectionnée :", db.name)
