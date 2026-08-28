# Explication détaillée du script : `11_prepare_orders.py`

Ce script permet de générer un jeu de données relationnel simulé dans MongoDB pour les Travaux Pratiques (TP) sur les pipelines d'agrégation. Il crée deux collections : `customers` (clients) et `orders` (commandes avec des articles embarqués).

---

## 1. Importations et initialisation

```python
from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
import os
import random
import sys
```
- Importation des modules nécessaires : `MongoClient` pour MongoDB, `load_dotenv` pour les variables d'environnement, `Faker` pour générer des données factices, `os` et `sys` pour le système, et `random` pour l'aléatoire.

```python
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
```
- Charge l'URI de connexion MongoDB, vérifie sa présence (arrête le script avec `sys.exit` si absent), et initialise les collections `customers` et `orders` dans la base de données `training`.

---

## 2. Initialisation de Faker et nettoyage (Reset)

```python
fake = Faker("fr_FR")

# Reset pour un TP reproductible
print("Suppression des collections customers et orders si elles existent déjà...")
customers.drop()
orders.drop()
```
- `Faker("fr_FR")` : Initialise le générateur de fausses données en français.
- `customers.drop()` et `orders.drop()` : Suppriment les collections existantes pour repartir sur une base propre à chaque exécution, garantissant la reproductibilité du TP.

---

## 3. Génération des clients (`customers`)

```python
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
```
- Boucle de 50 itérations pour créer 50 clients.
- `fake.name()` et `fake.email()` : Génèrent un nom et un email réalistes.
- `random.choice(...)` : Assigne aléatoirement un segment client (`bronze`, `silver`, ou `gold`).
- `customers.insert_one(doc)` : Insère le client et récupère son identifiant `_id` stocké dans `customer_ids` pour l'associer aux commandes futures.

---

## 4. Génération des commandes et articles embarqués (`orders`)

```python
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
- Boucle de 300 itérations pour créer 300 commandes.
- `random.choice(customer_ids)` : Associe la commande à un client existant aléatoire.
- `nb_items = random.randint(1, 5)` : Génère entre 1 et 5 articles par commande.
- Boucle interne pour créer chaque article (`items`) avec un nom de produit factice, un prix unitaire (`unit_price`) entre 10 et 300 €, et une quantité (`quantity`) entre 1 et 5.
- `order` : Dictionnaire regroupant le `customer_id`, la date (`fake.date_time_this_year()`), le statut aléatoire parmi `CONFIRMED`, `PENDING`, `CANCELLED`, et la liste des articles embarqués (`items`).
- `orders.insert_one(order)` : Insère chaque commande dans la collection `orders`.
