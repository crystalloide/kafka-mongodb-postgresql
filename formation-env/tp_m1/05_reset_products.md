# Explication détaillée du script : `05_reset_products.py`

Ce script utilitaire permet de vider entièrement une collection MongoDB (`products`) tout en affichant des statistiques avant et après l'opération (comptage des documents).

---

## 1. Importations et initialisation

```python
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
```
- Importation standard des modules nécessaires pour la connexion (`MongoClient`, `load_dotenv`, `os`, `sys`).

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
- Chargement de l'environnement, vérification de l'URI et sélection de la collection `products` de la base `training`.

---

## 2. Mesure, suppression et vérification

```python
avant = products.count_documents({})
result = products.delete_many({})
apres = products.count_documents({})
```
- `avant = products.count_documents({})` : Compte et stocke le nombre total de documents présents dans la collection avant la suppression.
- `result = products.delete_many({})` : Supprime **tous** les documents de la collection (le filtre vide `{}` cible l'ensemble). L'objet `result` retourne des métadonnées sur la suppression (notamment `deleted_count`).
- `apres = products.count_documents({})` : Compte le nombre de documents restants après l'opération (devrait être égal à 0).

---

## 3. Affichage du rapport

```python
print(f"Documents avant : {avant}")
print(f"Documents supprimés : {result.deleted_count}")
print(f"Documents restants : {apres}")
```
- Affiche un résumé clair indiquant le nombre initial de documents, le nombre effectif de documents supprimés via `result.deleted_count`, et l'état final de la collection.
