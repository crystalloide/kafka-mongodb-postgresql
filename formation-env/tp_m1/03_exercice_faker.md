# Explication détaillée du script : `03_exercice_faker.py`

Ce script permet de générer un jeu de données de test réaliste et volumineux (500 documents) en utilisant la bibliothèque `faker` et de l'insérer dans MongoDB, tout en créant des index pour optimiser les performances.

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
- `Faker` : Bibliothèque tierce permettant de générer de fausses données réalistes (textes, noms, adresses, etc.).
- `random` : Module standard Python pour générer des nombres aléatoires et faire des choix aléatoires parmi des listes.

```python
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :
"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]
```
- Chargement de l'environnement, vérification de l'URI de connexion et initialisation de la collection `products` (identique au script précédent).

---

## 2. Configuration de Faker et réinitialisation de la collection

```python
fake = Faker("fr_FR")
```
- Initialise l'instance `Faker` configurée pour la locale française (`"fr_FR"`), ce qui génère des données adaptées au contexte francophone.

```python
# Reset pour un TP reproductible
products.drop()
```
- `products.drop()` : Supprime complètement la collection et ses index existants. Cela garantit que chaque exécution du script part d'une base propre, rendant les Travaux Pratiques (TP) reproductibles.

---

## 3. Génération des données factices (Bulk data generation)

```python
categories = ["informatique", "mobilier", "papeterie", "electromenager", "jardin"]

documents = []
for _ in range(500):
    documents.append({
        "name": fake.catch_phrase(),
        "category": random.choice(categories),
        "price": round(random.uniform(5, 500), 2),
        "stock": random.randint(0, 200),
        "created_at": fake.date_time_this_year(),
    })
```
- `categories` : Liste prédéfinie de catégories de produits.
- `documents = []` : Initialisation d'une liste vide qui contiendra les 500 documents à insérer.
- `for _ in range(500):` : Boucle qui s'exécute 500 fois pour créer 500 documents distincts.
- `fake.catch_phrase()` : Génère un slogan accrocheur factice en français servant de nom de produit.
- `random.choice(categories)` : Sélectionne aléatoirement une catégorie parmi la liste.
- `round(random.uniform(5, 500), 2)` : Génère un nombre décimal aléatoire entre 5 et 500, arrondi à 2 décimales pour représenter un prix.
- `random.randint(0, 200)` : Génère un entier aléatoire compris entre 0 et 200 pour représenter le stock.
- `fake.date_time_this_year()` : Génère une date et heure aléatoire au cours de l'année courante.

---

## 4. Insertion en masse et création d'index

```python
result = products.insert_many(documents)
print(f"{len(result.inserted_ids)} produits insérés.")
```
- `products.insert_many(documents)` : Insère les 500 documents en une seule requête groupée (très performant).
- `len(result.inserted_ids)` : Affiche le nombre exact de documents insérés avec succès.

```python
products.create_index("name")
products.create_index("price")
```
- `products.create_index(...)` : Crée des index B-Tree sur les champs `name` et `price`. Cela accélère considérablement les recherches et les tris basés sur ces attributs lors des requêtes ultérieures.
