from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))

# Vérifier que le serveur répond
print(client.admin.command("ping"))

# Lister les bases existantes
print("Bases disponibles :", client.list_database_names())

# Créer/obtenir la base "training" (elle n'existe réellement
# qu'après la première écriture dans une collection)
db = client["training"]
print("Base sélectionnée :", db.name)