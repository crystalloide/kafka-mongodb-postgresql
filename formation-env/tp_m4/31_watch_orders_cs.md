# Explication détaillée du script : 31_watch_orders_cs.py

Ce document détaille le code source du script Python illustrant l'écoute en temps réel des modifications (Change Streams) sur une collection MongoDB.

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
from bson.json_util import dumps
from pymongo.errors import PyMongoError

load_dotenv()
```
- `from pymongo import MongoClient`: Importe le client MongoDB.
- `from dotenv import load_dotenv`: Charge les variables d'environnement.
- `import os`, `import sys`: Modules système pour vérifier l'environnement.
- `from bson.json_util import dumps`: Permet de sérialiser proprement les objets BSON (comme les ObjectId et dates) en JSON.
- `from pymongo.errors import PyMongoError`: Gestion des erreurs spécifiques à PyMongo.
- `load_dotenv()`: Charge le fichier `.env`.

### 2. Récupération et validation de l'URI MongoDB
```python
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
```
- Récupère l'URI MongoDB (qui doit impérativement inclure le paramètre `replicaSet=rs0` pour activer les Change Streams).
- Établit la connexion avec le client MongoDB et cible la collection `orders_cs`.

### 3. Définition du pipeline de filtrage
```python
# Pipeline : on ne garde que insert et update
pipeline = [
    {
        "$match": {
            "operationType": {"$in": ["insert", "update"]}
        }
    }
]
```
- Crée un pipeline d'agrégation appliqué au Change Stream pour filtrer et ne conserver que les événements de type insertion (`insert`) et mise à jour (`update`).

### 4. Écoute active du Change Stream et affichage des événements
```python
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
```
- `orders_cs.watch(...)`: Ouvre un flux d'écoute en temps réel avec le paramètre `full_document="updateLookup"` permettant d'obtenir l'état complet du document après une modification.
- `for change in stream:`: Boucle bloquante qui intercepte chaque nouvel événement en temps réel.
- `dumps(full_doc, ...)`: Affiche le document complet au format JSON lisible.
- `change["updateDescription"]["updatedFields"]`: Pour les opérations de mise à jour, isole et affiche précisément les champs qui ont changé.
- `stream.resume_token`: Affiche le jeton de reprise (`resume_token`), indispensable pour reprendre l'écoute en cas de coupure réseau ou de redémarrage de l'application.
- `except PyMongoError as e`: Intercepte proprement toute erreur liée au driver MongoDB.
