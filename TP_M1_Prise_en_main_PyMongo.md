## TP M1 — Prise en main & driver PyMongo

**Durée** : 45 min

**Prérequis** : 
- MongoDB 7.0.7 démarré (Docker Compose)
- venv activé
- `pymongo>=4.7,<5`
- `python-dotenv`
- `faker` installés (`requirements.txt`)
- fichier `.env` créé

## Objectifs

- Se connecter à MongoDB depuis Python avec `MongoClient`, **avec authentification**.
- Explorer bases et collections existantes.
- Réaliser les opérations CRUD de base sur une collection.
- Manipuler filtres, tri et pagination sur un jeu de données généré.

---

## 0. Configuration du `.env` (5 min)

Le conteneur `mongodb` du `docker-compose.yml` est démarré avec :

```yaml
environment:
  MONGO_INITDB_ROOT_USERNAME: formation
  MONGO_INITDB_ROOT_PASSWORD: formation
  MONGO_INITDB_DATABASE: formation
```

Dès qu'un `MONGO_INITDB_ROOT_USERNAME` est défini, MongoDB démarre avec l'**authentification activée**. Une connexion sans identifiants (`mongodb://localhost:27017`) échouera donc systématiquement.

Vérifier que le fichier `.env` à la racine du TP contient :

```
MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin
```

**Point important** : `formation` est un *root user*, créé dans la base `admin` (c'est la base où MongoDB stocke les comptes root à la création). Il faut donc obligatoirement le paramètre `authSource=admin` dans l'URI — même si l'on travaille ensuite dans la base `training`. Sans ce paramètre, MongoDB tente d'authentifier l'utilisateur dans la base cible de l'URI (par défaut `admin` aussi si non précisée, mais le comportement diffère selon les versions du driver) et l'authentification échoue silencieusement côté logique métier, avec une erreur `OperationFailure`.


### Pré-requis

###  0. Préparation VS Code & environnement Python (30 min, transverse)

Objectif : chaque stagiaire a un environnement fonctionnel avant de commencer les TP techniques.

- Vérifier que tous les conteneurs sont `Up (healthy)` :
```bash
su - user 
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
docker compose ps
```

- Installation python :
```bash
sudo apt update
sudo apt install python-is-python3
```
Vérifiez ensuite :
```bash
python --version
```

- Créer un venv dédié :
```bash
python -m venv .venv && source .venv/bin/activate
```

- Fichier `requirements.txt` à créer
```bash
vi requirements.txt
```
- avec le contenu suivant :
```bash
kafka-python==2.3.1
pymongo>=4.7,<5
psycopg2-binary
python-dotenv
faker
```

- Mettre à jour pip (évite des erreurs de résolution de dépendances) :
```bash
pip install --upgrade pip
```

- Installer les paquets :
```bash
pip install -r requirements.txt
```

- Vérifier l'installation :
```bash
pip list
```

Vous devez voir les 5 paquets avec leurs versions.
```text
Package         Version
--------------- -------
dnspython       2.8.0
Faker           40.36.0
kafka-python    2.3.1
pip             26.2.1
psycopg2-binary 2.9.12
pymongo         4.17.0
python-dotenv   1.2.2

```

- Extensions VS Code : Python (Microsoft), Docker, MongoDB for VS Code, YAML, Thunder Client (pour tester Kafka Connect REST API).

- Fichier `.env` avec les endpoints :
```bash
cp ~/kafka-mongodb-postgresql/formation-env/tp_m1/env .env
cat .env
```

```text
# Endpoints environnement de formation Kafka / MongoDB / CQRS
# A charger avec python-dotenv (load_dotenv())

# Kafka - cluster KRaft 3 noeuds (controller/broker)
# Port host different par broker (listener PLAINTEXT_HOST) :
# kafka1 -> 9092, kafka2 -> 9094, kafka3 -> 9096
# (9093 est le port interne du listener CONTROLLER, jamais expose a l'hote)
KAFKA_BOOTSTRAP=localhost:9092,localhost:9094,localhost:9096

# MongoDB - noeud unique, utilisateur root cree via MONGO_INITDB_ROOT_USERNAME/PASSWORD
MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin

# Consoles de supervision / UI
KAFKA_UI=http://localhost:8080
HAWTIO=http://localhost:8888/hawtio
REDPANDA_CONSOLE=http://localhost:8090

# Kafka Connect (REST API) - utile pour tester via Thunder Client
KAFKA_CONNECT=http://localhost:8083
```

- Vérification rapide avec script `check_env.py` qui teste la connexion Kafka (métadonnées cluster) et MongoDB (`ping`) et affiche un résumé OK/KO.


```bash
python check_env.py
```

---

## 1. Connexion et exploration (10 min)

Créez un fichier `01_connexion.py` :

```python
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
```

**À observer** : tant qu'aucun document n'est inséré, `training` n'apparaîtra pas dans `list_database_names()`. C'est une particularité de MongoDB (création paresseuse des bases/collections).

**Question** : que se passe-t-il si `MONGO_URI` pointe vers un port erroné (ex. `27018`) ? Testez et observez le type d'exception levée (`pymongo.errors.ServerSelectionTimeoutError`).

**Question complémentaire** : que se passe-t-il si le port est correct mais le mot de passe est erroné ? Faites tester les deux cas aux stagiaires pour qu'ils distinguent bien :
- `ServerSelectionTimeoutError` → problème réseau/host/port (le serveur n'a pas pu être atteint).
- `OperationFailure` (`Authentication failed`) → serveur atteint, mais identifiants ou `authSource` incorrects.


```bash
cd tp_m1
ls
```

```bash
python 01_connexion.py
```

---

## 2. CRUD de base sur `products` (20 min)

Créez `02_crud.py` :

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
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]

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

print("\nCreate : ajout de plusieurs produits : insert_many")
produits_liste = [
    {"name": "Souris sans fil", "category": "informatique", "price": 29.90, "stock": 100},
    {"name": "Ecran 27 pouces", "category": "informatique", "price": 199.00, "stock": 15},
    {"name": "Chaise de bureau", "category": "mobilier", "price": 149.50, "stock": 8},
]
result = products.insert_many(produits_liste)
print("\nIDs insérés :", result.inserted_ids)

# --- READ ---
print("\nRead : lecture d'un seul produit : find_one")
un_produit = products.find_one({"category": "mobilier"})
print("\nUn produit mobilier :", un_produit)

print("\nRead : lecture de plusieurs produits : find")
for p in products.find({"category": "informatique"}):
    print("\n", p["name"], p["price"])

# --- UPDATE ---
print("\nUpdate : mise à jour d'un seul produit : update_one")
products.update_one(
    {"name": "Clavier mecanique"},
    {"$set": {"price": 69.90}}
)

print("\nUpdate : mise à jour de plusieurs produits : update_many")
products.update_many(
    {"category": "informatique"},
    {"$inc": {"stock": -1}}
)

# --- DELETE ---
print("\nDelete : suppression de plusieurs produits : delete_many")
products.delete_many({"category": "mobilier"})

print("\nNombre de produits restants :", products.count_documents({}))

```

```bash
python 02_crud.py
```

**Points à préciser :** :
- `insert_one` retourne un `InsertOneResult` avec `inserted_id` (un `ObjectId` généré automatiquement si non fourni).
- `update_one`/`update_many` nécessitent un opérateur (`$set`, `$inc`, `$unset`, etc.) — un update sans opérateur remplace **tout** le document.
- `delete_many({})` supprimerait toute la collection : à manipuler avec précaution, bon moment pour parler de gouvernance/sécurité des opérations destructives.


---

## 3. Exercice — Jeu de données Faker + requêtes de filtrage (15 min)

### 3.1 Génération des données

Créez `03_exercice_faker.py` :

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
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

client = MongoClient(MONGO_URI)
db = client["training"]
products = db["products"]

fake = Faker("fr_FR")

# Reset pour un TP reproductible
products.drop()

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

result = products.insert_many(documents)
print(f"{len(result.inserted_ids)} produits insérés.")

products.create_index("name")
products.create_index("price")

```

```bash
python 03_exercice_faker.py
```

### 3.2 Les 5 requêtes à écrire

Complétez `04_requetes.py` avec les 5 requêtes suivantes (solutions fournies ci-dessous pour le corrigé formateur) :

```python
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os
import sys

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    sys.exit(
        "MONGO_URI introuvable. Vérifiez qu'un fichier .env existe dans le "
        "dossier tp_m1/ (à côté de ce script) et qu'il contient bien :\n"
        "MONGO_URI=mongodb://formation:formation@localhost:27017/?authSource=admin"
    )

products = MongoClient(MONGO_URI)["training"]["products"]

# 1. Produits dont le prix est compris entre 50 et 150 euros
q1 = products.find({"price": {"$gte": 50, "$lte": 150}})
print("Q1 - Plage de prix :", products.count_documents({"price": {"$gte": 50, "$lte": 150}}))

# 2. Produits dont le nom contient "solution" (insensible à la casse)
q2 = products.find({"name": {"$regex": "solution", "$options": "i"}})
print("Q2 - Regex sur nom :", products.count_documents({"name": {"$regex": "solution", "$options": "i"}}))

# 3. Les 10 produits les plus chers, triés par prix décroissant
q3 = products.find().sort("price", DESCENDING).limit(10)
print("Q3 - Top 10 prix décroissant :")
for p in q3:
    print(" -", p["name"], p["price"])

# 4. Pagination : page 3 avec 20 produits par page, triés par nom
page = 3
page_size = 20
q4 = products.find().sort("name", ASCENDING).skip((page - 1) * page_size).limit(page_size)
print(f"Q4 - Page {page} ({page_size} résultats/page) :", len(list(q4)))

# 5. Produits en rupture de stock (stock = 0) d'une catégorie donnée, triés par prix croissant
q5 = products.find({"category": "informatique", "stock": 0}).sort("price", ASCENDING)
print("Q5 - Rupture stock informatique :", products.count_documents({"category": "informatique", "stock": 0}))

```

```bash
python 04_requetes.py
```

---

## Points de vigilance pédagogique

- Rappeler que `find()` retourne un **curseur paresseux** (lazy) : les documents ne sont chargés qu'à l'itération. `count_documents()` est l'API moderne recommandée (remplace l'ancien `count()` déprécié).
- La pagination par `skip/limit` est simple mais coûteuse sur de gros volumes (MongoDB doit parcourir les documents ignorés) : c'est l'occasion d'annoncer le TP M3 sur les index et la pagination par curseur (`range pagination` avec `_id` ou champ indexé).
- Vérifier avec les stagiaires que l'index créé sur `price` (TP M3 anticipé) accélère bien la requête Q1/Q3 via `explain()`.
- Insister sur `authSource=admin` : c'est l'erreur la plus fréquente en atelier (les stagiaires copient souvent un URI trouvé en ligne sans ce paramètre, ou omettent les identifiants).

## Livrable stagiaire attendu

Un dossier `tp_m1/` contenant `.env` (non versionné, basé sur `.env.example`) et les 4 scripts (`01_connexion.py` à `04_requetes.py`) fonctionnels, exécutables depuis le venv du poste, avec les résultats imprimés en console pour chacune des 5 requêtes.
