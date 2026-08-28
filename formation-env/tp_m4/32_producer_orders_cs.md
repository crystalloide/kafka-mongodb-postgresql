# Explication détaillée du script : 32_producer_orders_cs.py

Ce document détaille le code source du script Python simulant une activité applicative (insertions et mises à jour continues de commandes) pour alimenter un Change Stream MongoDB.

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import sys
import random
import time

load_dotenv()
```
- `from faker import Faker`: Importe la bibliothèque pour générer des données factices réalistes (noms, etc.).
- `random`, `time`: Modules pour générer de l'aléa et gérer les pauses temporelles.

### 2. Validation de l'URI et connexion à MongoDB
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

fake = Faker("fr_FR")
```
- Vérifie la présence de `MONGO_URI` (nécessitant le replica set `rs0`).
- Initialise la connexion et configure `Faker` en français (`fr_FR`) pour des noms de clients réalistes.

### 3. Réinitialisation de la collection et insertion initiale
```python
print("Reset de la collection training.orders_cs...")
orders_cs.drop()

print("Insertion de commandes initiales...")
order_ids = []
for i in range(10):
    doc = {
        "order_ref": f"CMD-{1000 + i}",
        "customer_name": fake.name(),
        "status": random.choice(["NEW", "PROCESSING", "COMPLETED"]),
        "amount": round(random.uniform(50, 500), 2),
    }
    result = orders_cs.insert_one(doc)
    order_ids.append(result.inserted_id)

print(f"{len(order_ids)} commandes insérées.\n")
```
- Supprime la collection `orders_cs` pour repartir sur une base propre.
- Insère 10 commandes initiales avec des données aléatoires et conserve leurs identifiants (`_id`) dans la liste `order_ids` pour pouvoir les modifier ultérieurement.

### 4. Boucle de production (Insertions et Mises à jour continues)
```python
print("Boucle de production : insert + update toutes les 2 secondes.")
print("Appuyez sur Ctrl+C pour arrêter.\n")

try:
    while True:
        # INSERT d'une nouvelle commande
        doc = {
            "order_ref": f"CMD-{random.randint(2000, 9999)}",
            "customer_name": fake.name(),
            "status": "NEW",
            "amount": round(random.uniform(50, 500), 2),
        }
        result = orders_cs.insert_one(doc)
        print(f"[INSERT] Nouvelle commande {doc['order_ref']} (id={result.inserted_id})")

        # UPDATE sur une commande existante
        if order_ids:
            target_id = random.choice(order_ids)
            new_status = random.choice(["PROCESSING", "COMPLETED", "CANCELLED"])
            new_amount = round(random.uniform(50, 500), 2)
            orders_cs.update_one(
                {"_id": target_id},
                {
                    "$set": {
                        "status": new_status,
                        "amount": new_amount,
                    }
                },
            )
            print(
                f"[UPDATE] Commande id={target_id} -> "
                f"status={new_status}, amount={new_amount}"
            )

        time.sleep(2)
except KeyboardInterrupt:
    print("\nArrêt du producteur.")
```
- `while True:`: Boucle infinie simulant l'activité de l'application.
- `orders_cs.insert_one(doc)`: Insère une nouvelle commande avec un statut initial `"NEW"`.
- `orders_cs.update_one(...)`: Met à jour aléatoirement l'une des commandes existantes de la liste `order_ids` en changeant son statut et son montant.
- `time.sleep(2)`: Pause de 2 secondes entre chaque itération pour observer clairement les événements côté consommateur.
- `except KeyboardInterrupt:`: Permet d'interrompre proprement le script via `Ctrl+C`.
