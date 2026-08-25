## TP M4 — Change Streams avec PyMongo

**Durée** : 45 min

**Prérequis** :
- TP M1 à M3 réalisés (base `training` créée, environnement Python fonctionnel).
- MongoDB 7.0.7 démarré en **réplica set** (obligatoire pour les change streams).
- venv activé.
- `pymongo>=4.7,<5`, `faker`, `python-dotenv` installés (`requirements.txt`).
- fichier `.env` avec `MONGO_URI` configuré

- **Bien dérouler les instructions en pré-requis données dans le répertoire t4_m4** formation-env/tp_m4/Prerequis_MongoDB_en_ReplicaSet.md

## Objectifs

- Ouvrir un change stream avec `collection.watch()` pour capter les insertions/mises à jour en temps réel.
- Mettre en place un **consommateur** qui affiche les événements (opération, document complet, champs modifiés).
- Mettre en place un **producteur** qui insère/met à jour des documents pour alimenter le flux — brique de préparation conceptuelle au CQRS / CDC.

---

## 0. Rappel — Change Streams MongoDB (5–10 min)

Les **change streams** permettent de recevoir en temps réel les changements (insert, update, delete, replace, etc.) sur une collection, une base ou l'ensemble du cluster MongoDB.

Ils reposent sur le journal d'opérations (oplog) d'un **réplica set** : il faut donc que MongoDB soit démarré en réplica set, même avec un seul nœud.

Avec PyMongo, on utilise la méthode `watch()` sur une collection, puis on itère sur le curseur pour recevoir les événements au fil de l'eau.

---

### On se positionne dans le répertoire du TP 4 : 

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_m4
ls
```

## 1. Consommateur — script `31_watch_orders_cs.py` (20 min)

Objectif : ouvrir un change stream sur une collection `orders_cs` dans la base `training` et afficher les événements en temps réel.

Créez le fichier `31_watch_orders_cs.py` :

```python
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
```

Exécutez le script dans une première console :

```bash
python 31_watch_orders_cs.py
```

Vous devez voir le message d'ouverture du change stream, puis le script se mettre en attente de nouveaux événements.

### Points pédagogiques

- `watch()` retourne un **cursor de type change stream** : la boucle `for change in stream` reste bloquante tant qu'aucun événement n'arrive.
- Le `pipeline` permet de filtrer les événements (ici, uniquement `insert` et `update`).
- `full_document="updateLookup"` permet de récupérer le document complet après une mise à jour, pratique pour des projections CQRS.

---


## 2. Producteur — script `32_producer_orders_cs.py` (20 min)

Objectif : insérer et mettre à jour des documents dans `training.orders_cs` pour générer des événements consommés par le change stream.

Créez le fichier `32_producer_orders_cs.py` :

```python
from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import sys
import random
import time

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

fake = Faker("fr_FR")

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

Exécutez le script dans une deuxième console :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
cd tp_m4
```

```bash
python 32_producer_orders_cs.py
```

À chaque insert/update, le script consommateur (`31_watch_orders_cs.py`) affiche l'événement correspondant.

### Points pédagogiques

- Le producteur joue le rôle d'une **application métier** qui génère des événements.
- Le consommateur est une brique de **CDC** (Change Data Capture) : il pourrait alimenter une vue CQRS dans une autre base ou un autre système.
- La boucle infinie avec `time.sleep(2)` permet de voir clairement les événements arriver dans la console du consommateur.

---

## 3. Exercice guidé et variantes (5–10 min)

Proposez aux stagiaires :

1. **Filtrer les événements sur un champ métier** :
   - Ajouter un champ `type` (ex. `"ONLINE"` vs `"STORE"`) dans les commandes.
   - Adapter le `pipeline` du change stream pour ne recevoir que les commandes `type = "ONLINE"`.

2. **Limiter l'affichage** :
   - N'afficher que certaines propriétés (`order_ref`, `status`, `amount`) pour simuler une projection vers une vue de lecture.

3. **Discussion sur la reprise** :
   - Montrer le `resume_token` dans la console.
   - Expliquer qu'il permet de reprendre un change stream après une coupure réseau ou un redéploiement, ce qui est essentiel dans une architecture CQRS/CDC.

Ce TP M4 sert de pont naturel vers les TPs Kafka/CQRS de l'après-midi : on passe d'une capture de changements MongoDB à des flux d'événements métier utilisables pour construire des vues de lecture dénormalisées.
