from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
from bson.json_util import dumps
from pymongo.errors import PyMongoError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier du projet et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
orders_cs = db["orders_cs"]

print("Ouverture du change stream sur training.orders_cs...")
print("Appuyez sur Ctrl+C pour arrêter.\n")

# Pipeline : on ne garde que insert et update
pipeline = [
    {
        "$match": {
            "operationType": {"$in": ["insert", "update"]}
        }
    }
]

try:
    # full_document='updateLookup' pour avoir le document complet après update
    with orders_cs.watch(pipeline=pipeline, full_document="updateLookup") as stream:
        for change in stream:
            print("=" * 80)
            print("operationType :", change["operationType"])
            full_doc = change.get("fullDocument")
            if full_doc:
                print("fullDocument :")
                print(dumps(full_doc, indent=2, ensure_ascii=False))

            if change["operationType"] == "update":
                print("Champs modifiés :")
                print(
                    dumps(
                        change["updateDescription"]["updatedFields"],
                        indent=2,
                        ensure_ascii=False,
                    )
                )

            # Optionnel : afficher le resume_token pour parler de reprise
            print("\nresume_token :", stream.resume_token)
except PyMongoError as e:
    print("Erreur dans le change stream :", e)