# Explication détaillée du script : `02_crud.py`

Ce script présente les opérations fondamentales **CRUD** (Create, Read, Update, Delete) avec la base de données NoSQL **MongoDB** en utilisant le pilote Python `pymongo`.

---

## 1. Importations et configuration initiale

```python
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
```
- `from pymongo import MongoClient` : Importe la classe principale `MongoClient` du pilote PyMongo pour se connecter à un serveur MongoDB.
- `from dotenv import load_dotenv` : Importe la fonction `load_dotenv` pour charger les variables d'environnement depuis un fichier `.env`.
- `import os` : Permet d'interagir avec le système d'exploitation (notamment pour récupérer les variables d'environnement).
- `import sys` : Permet d'accéder à des paramètres et fonctions spécifiques au système (utilisé ici pour interrompre l'exécution en cas d'erreur).

```python
load_dotenv()
```
- Charge les variables définies dans le fichier `.env` (situé dans le répertoire courant ou parent) dans l'environnement d'exécution (`os.environ`).

```python
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :
"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )
```
- `os.getenv("MONGO_URI")` : Récupère la valeur de la variable d'environnement `MONGO_URI`.
- `if not MONGO_URI:` : Vérifie si la variable est vide ou absente.
- `sys.exit(...)` : Arrête immédiatement le script et affiche un message d'aide explicatif si l'URI de connexion est manquante.

---

## 2. Connexion à MongoDB et sélection des collections

```python
client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]
```
- `client = MongoClient(MONGO_URI)` : Initialise la connexion au serveur MongoDB avec l'URI de connexion récupérée.
- `db = client["training"]` : Sélectionne la base de données nommée `training` (créée à la volée par MongoDB si elle n'existe pas encore).
- `products = db["products"]` : Sélectionne la collection `products` au sein de la base de données `training`.

---

## 3. Section CREATE (Création / Insertion de documents)

```python
# --- CREATE ---
print("\nCreate : ajout d'un seul produit : insert_one")
produit = {
    "name": "Clavier mecanique",
    "category": "informatique",
    "price": 79.90,
    "stock": 25,
}
result = products.insert_one(produit)
print("\nInséré avec _id :", result.inserted_id)
```
- `produit` : Dictionnaire Python représentant un document JSON à insérer.
- `products.insert_one(produit)` : Insère un document unique dans la collection `products`.
- `result.inserted_id` : Récupère l'identifiant unique (`_id`) généré automatiquement par MongoDB pour ce nouveau document.

```python
print("\nCreate : ajout de plusieurs produits : insert_many")
produits_liste = [
    {"name": "Souris sans fil", "category": "informatique", "price": 29.90, "stock": 100},
    {"name": "Ecran 27 pouces", "category": "informatique", "price": 199.00, "stock": 15},
    {"name": "Chaise de bureau", "category": "mobilier", "price": 149.50, "stock": 8},
]
result = products.insert_many(produits_liste)
print("\nIDs insérés :", result.inserted_ids)
```
- `produits_liste` : Une liste de dictionnaires représentant plusieurs documents.
- `products.insert_many(produits_liste)` : Insère tous les documents de la liste en une seule opération de lot.
- `result.inserted_ids` : Retourne la liste de tous les identifiants uniques (`_id`) générés pour les documents insérés.

---

## 4. Section READ (Lecture / Requêtage)

```python
# --- READ ---
print("\nRead : lecture d'un seul produit : find_one")
un_produit = products.find_one({"category": "mobilier"})
print("\nUn produit mobilier :", un_produit)
```
- `products.find_one({...})` : Recherche et retourne le premier document correspondant au critère de filtre (ici, `category` égal à `"mobilier"`).

```python
print("\nRead : lecture de plusieurs produits : find")
for p in products.find({"category": "informatique"}):
    print("\n", p["name"], p["price"])
```
- `products.find({...})` : Retourne un curseur parcourant tous les documents correspondant au filtre (`category` égal à `"informatique"`).
- `for p in ...:` : Parcourt chaque document du curseur et affiche son nom et son prix.

---

## 5. Section UPDATE (Mise à jour)

```python
# --- UPDATE ---
print("\nUpdate : mise à jour d'un seul produit : update_one")
products.update_one(
    {"name": "Clavier mecanique"},
    {"$set": {"price": 69.90}}
)
```
- `products.update_one(filtre, mise_a_jour)` : Modifie le premier document trouvé correspondant au filtre (`name` égal à `"Clavier mecanique"`).
- `{"$set": {"price": 69.90}}` : L'opérateur `$set` permet de mettre à jour la valeur du champ `price` à `69.90` sans modifier les autres champs.

```python
print("\nUpdate : mise à jour de plusieurs produits : update_many")
products.update_many(
    {"category": "informatique"},
    {"$inc": {"stock": -1}}
)
```
- `products.update_many(...)` : Applique la modification à **tous** les documents répondant au critère de filtre.
- `{"$inc": {"stock": -1}}` : L'opérateur `$inc` décrémente (incrémente d'une valeur négative) le champ `stock` de 1 pour chaque produit de la catégorie `"informatique"`.

---

## 6. Section DELETE (Suppression) et Statistiques

```python
# --- DELETE ---
print("\nDelete : suppression de plusieurs produits : delete_many")
products.delete_many({"category": "mobilier"})
```
- `products.delete_many({...})` : Supprime tous les documents de la collection qui satisfont le critère (ici, tous les produits de la catégorie `"mobilier"`).

```python
print("\nNombre de produits restants :", products.count_documents({}))
```
- `products.count_documents({})` : Compte le nombre total de documents dans la collection (un filtre vide `{}` cible l'ensemble des documents).
