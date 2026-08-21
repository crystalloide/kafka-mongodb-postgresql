## TP M2 — Modélisation de documents & agrégation

**Durée** : 45 min

**Prérequis** :
- TP M1 réalisé (base `training` créée, environnement Python fonctionnel).
- MongoDB 7.0.7 démarré (Docker Compose).
- venv activé.
- `pymongo>=4.7,<5`, `faker`, `python-dotenv` installés (`requirements.txt`).
- fichier `.env` avec `MONGO_URI` configuré (même valeur que pour le TP M1).

## Objectifs

- Comprendre la différence entre **modèle embarqué** et **modèle référencé** dans MongoDB.
- Manipuler un **pipeline d'agrégation** complet : `$match`, `$unwind`, `$group`, `$lookup`, `$project`, `$sort`.
- Calculer le **chiffre d'affaires par client et par mois** à partir d'une collection `orders` préchargée.

---

## 0. Rappel — Modèle embarqué vs référencé (10 min)

Dans MongoDB, il est possible de modéliser une commande de deux façons principales :

1. **Modèle embarqué** : toutes les lignes de commande sont stockées dans un tableau `items` à l'intérieur du document `orders`.
2. **Modèle référencé** : les lignes de commande sont stockées dans une collection séparée `order_lines`, qui référence la commande par une clé `order_id`.

### Exemple de modèle embarqué (collection `orders`)

```json
{
  "_id": ObjectId("..."),
  "customer_id": ObjectId("..."),
  "order_date": ISODate("2026-08-10T10:15:00Z"),
  "status": "CONFIRMED",
  "items": [
    {
      "product_name": "Clavier mécanique",
      "unit_price": 79.90,
      "quantity": 2
    },
    {
      "product_name": "Souris sans fil",
      "unit_price": 29.90,
      "quantity": 1
    }
  ]
}
```

### Exemple de modèle référencé (`orders` + `order_lines`)

```json
// orders
{
  "_id": ObjectId("..."),
  "customer_id": ObjectId("..."),
  "order_date": ISODate("2026-08-10T10:15:00Z"),
  "status": "CONFIRMED"
}

// order_lines
{
  "_id": ObjectId("..."),
  "order_id": ObjectId("..."),
  "product_name": "Clavier mécanique",
  "unit_price": 79.90,
  "quantity": 2
}
```

### Questions à discuter avec les stagiaires

- Dans quels cas le modèle embarqué est-il plus simple et plus performant ?
- Quand le modèle référencé devient-il nécessaire (taille des documents, réutilisation des lignes de commande, besoins d'agrégation avancés) ?
- Quel modèle est le plus adapté à une vue de lecture CQRS où l'on veut répondre rapidement à des requêtes comme « commandes d'un client sur une période » ?

---

## On se positionne dans le répertoire du TP 2 :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_m2
ls
```


## 1. Préparation des collections `customers` et `orders` (10 min)

Objectif : créer un jeu de données réaliste avec des clients et des commandes, en utilisant Faker. Les commandes utiliseront le **modèle embarqué** avec un tableau `items`.

Créez le fichier `11_prepare_orders.py` :

```python
from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import random
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

customers = db["customers"]
orders = db["orders"]

fake = Faker("fr_FR")

# Reset pour un TP reproductible
print("Suppression des collections customers et orders si elles existent déjà...")
customers.drop()
orders.drop()

# Génération de ~50 clients
print("Insertion des clients...")
customer_ids = []
for _ in range(50):
    doc = {
        "full_name": fake.name(),
        "email": fake.email(),
        "segment": random.choice(["bronze", "silver", "gold"]),
    }
    result = customers.insert_one(doc)
    customer_ids.append(result.inserted_id)

print(f"{len(customer_ids)} clients insérés.")

# Génération de ~300 commandes avec items embarqués
print("Insertion des commandes...")
statuses = ["CONFIRMED", "PENDING", "CANCELLED"]

order_count = 0
for _ in range(300):
    customer_id = random.choice(customer_ids)
    nb_items = random.randint(1, 5)
    items = []
    for _ in range(nb_items):
        unit_price = round(random.uniform(10, 300), 2)
        quantity = random.randint(1, 5)
        items.append(
            {
                "product_name": fake.catch_phrase(),
                "unit_price": unit_price,
                "quantity": quantity,
            }
        )

    order = {
        "customer_id": customer_id,
        "order_date": fake.date_time_this_year(),
        "status": random.choice(statuses),
        "items": items,
    }

    orders.insert_one(order)
    order_count += 1

print(f"{order_count} commandes insérées.")
print("Jeu de données customers/orders prêt pour les agrégations.")
```

Exécutez le script :

```bash
python 11_prepare_orders.py
```

Vérifiez dans MongoDB (via MongoDB for VS Code ou `mongosh`) que les collections `customers` et `orders` ont été créées et contiennent des documents.

```bash
mongosh "mongodb://formation:formation@localhost:27017/?authSource=admin"
```

```scriptMongosh
use training
db.customers.find().limit(10).pretty()
```

```scriptMongosh
db.orders.find().limit(10).pretty()
```

---

## 2. Pipeline d'agrégation — CA par client et par mois (25 min)

Objectif : calculer le **chiffre d'affaires** par client et par mois en se basant sur la collection `orders` (modèle embarqué), en ne prenant en compte que les commandes `status = "CONFIRMED"`.

### Étapes du pipeline

1. `$match` : filtrer les commandes confirmées.
2. `$unwind` : aplatir le tableau `items` pour traiter chaque ligne de commande individuellement.
3. `$group` : regrouper par client + année + mois et sommer `unit_price * quantity`.
4. `$lookup` : joindre la collection `customers` pour récupérer le nom du client.
5. `$project` : formater le résultat (nom du client, année, mois, CA).
6. `$sort` : trier par année/mois puis par nom de client.

Créez le fichier `12_ca_par_client_mois.py` :

```python
from pymongo import MongoClient
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

orders = db["orders"]

pipeline = [
    {"$match": {"status": "CONFIRMED"}},
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": {
                "customer_id": "$customer_id",
                "year": {"$year": "$order_date"},
                "month": {"$month": "$order_date"},
            },
            "revenue": {
                "$sum": {
                    "$multiply": ["$items.unit_price", "$items.quantity"]
                }
            },
        }
    },
    {
        "$lookup": {
            "from": "customers",
            "localField": "_id.customer_id",
            "foreignField": "_id",
            "as": "customer",
        }
    },
    {"$unwind": "$customer"},
    {
        "$project": {
            "_id": 0,
            "customer_id": "$_id.customer_id",
            "customer_name": "$customer.full_name",
            "year": "$_id.year",
            "month": "$_id.month",
            "revenue": 1,
        }
    },
    {"$sort": {"year": 1, "month": 1, "customer_name": 1}},
]

results = list(orders.aggregate(pipeline))

if not results:
    print("Aucun résultat : vérifiez que des commandes CONFIRMED existent dans la collection orders.")
else:
    print(f"Nombre de lignes de CA client/mois : {len(results)}")
    print("\nAperçu des 20 premières lignes :\n")
    for doc in results[:20]:
        print(
            f"{doc['year']}-{doc['month']:02d} | "
            f"{doc['customer_name']} | CA = {doc['revenue']:.2f} €"
        )
```

Exécutez le script :

```bash
python 12_ca_par_client_mois.py
```

### Questions pour les stagiaires

- Que se passe-t-il si l'on **supprime** l'étape `$unwind` du pipeline ? Les résultats sont-ils encore cohérents ?
- Comment filtrer uniquement les clients du segment `"gold"` dans ce pipeline ? (Indice : ajouter un `$match` après le `$lookup` sur `customers`.)
- Comment adapter ce pipeline pour calculer le CA **par mois uniquement**, sans détail par client (changer les clés du `$group`).

---

## 3. Synthèse pédagogique

- Le modèle embarqué permet des lectures rapides de commandes complètes et simplifie les agrégations centrées sur la commande.
- Le pipeline d'agrégation MongoDB est une brique essentielle pour construire des **vues de lecture** dérivées (préparation à la partie CQRS de la formation).
- `$lookup` reste possible mais doit être utilisé avec parcimonie pour éviter les jointures coûteuses sur de gros volumes : dans les architectures CQRS, on préfère souvent des vues matérialisées dédiées à la lecture.
