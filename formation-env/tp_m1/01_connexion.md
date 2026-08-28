# Explication détaillée du script : `01_connexion.py`

Ce script effectue un test de connectivité rapide et de validation des identifiants d'authentification sur le serveur MongoDB.

---

## 1. Importations et initialisation de l'URI

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
```
- Importe `MongoClient` et les exceptions spécifiques (`OperationFailure` pour les erreurs d'authentification/droits, `ServerSelectionTimeoutError` pour les problèmes réseau).
- Définit une URI par défaut pointant vers l'instance MongoDB locale de formation si la variable d'environnement n'est pas définie.
- Initialise le client MongoDB.

---

## 2. Test de connectivité et d'authentification

```python
# Vérifier que le serveur répond ET que l'authentification est valide
try:
    print(client.admin.command("ping"))
except ServerSelectionTimeoutError:
    print("Connexion impossible : vérifiez host/port dans MONGO_URI.")
    raise
except OperationFailure:
    print("Authentification refusée : vérifiez user/password/authSource dans MONGO_URI.")
    raise
```
- `client.admin.command("ping")` : Envoie une commande `ping` à la base d'administration du serveur.
- `ServerSelectionTimeoutError` : Intercepte les erreurs si le serveur est injoignable (mauvais port, conteneur arrêté).
- `OperationFailure` : Intercepte les refus d'authentification (mauvais nom d'utilisateur, mot de passe incorrect, `authSource` manquant).
- `raise` : Propage l'exception après affichage du message explicatif.

---

## 3. Exploration des bases de données et sélection

```python
# Lister les bases existantes
print("Bases disponibles :", client.list_database_names())
```
- `client.list_database_names()` : Récupère et affiche la liste de toutes les bases de données accessibles sur le serveur MongoDB.

```python
# Créer/obtenir la base "training" (elle n'existe réellement
# qu'après la première écriture dans une collection)
db = client["training"]
print("Base sélectionnée :", db.name)
```
- `client["training"]` : Sélectionne la base de données `training`. À noter que MongoDB ne crée physiquement la base sur le disque qu'au moment de la première écriture de données.
