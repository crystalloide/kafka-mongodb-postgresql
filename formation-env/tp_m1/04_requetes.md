# Explication détaillée du script : `04_requetes.py`

Ce script illustre des requêtes de recherche avancées dans MongoDB : filtrage par plages de valeurs, expressions régulières (regex), tris, limites, pagination robuste et requêtes multicritères.

---

## 1. Importations et connexion directe

```python
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os
import sys
```
- `ASCENDING`, `DESCENDING` : Constantes importées de PyMongo pour spécifier l'ordre de tri (croissant ou décroissant).

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

products = MongoClient(MONGO_URI)["training"]["products"]
```
- Connexion directe en une seule ligne chaînée : récupère le client, sélectionne la base `training` et la collection `products`.

---

## 2. Requête 1 : Plage de valeurs (`$gte`, `$lte`)

```python
# 1. Produits dont le prix est compris entre 50 et 150 euros
q1 = products.find({"price": {"$gte": 50, "$lte": 150}})
print("Q1 - Plage de prix :", products.count_documents({"price": {"$gte": 50, "$lte": 150}}))
```
- `{"$gte": 50, "$lte": 150}` : Opérateurs de comparaison signifiant respectivement *Greater Than or Equal* (supérieur ou égal à 50) et *Less Than or Equal* (inférieur ou égal à 150).
- `count_documents(...)` : Compte directement le nombre de documents correspondants sans charger les résultats en mémoire.

---

## 3. Requête 2 : Recherche textuelle par expression régulière (`$regex`)

```python
# 2. Produits dont le nom contient "solution" (insensible à la casse)
q2 = products.find({"name": {"$regex": "solution", "$options": "i"}})
print("Q2 - Regex sur nom :", products.count_documents({"name": {"$regex": "solution", "$options": "i"}}))
```
- `"$regex": "solution"` : Recherche les documents dont le champ `name` contient la sous-chaîne `"solution"`.
- `"$options": "i"` : Rend la recherche insensible à la casse (majuscules/minuscules indifférentes).

---

## 4. Requête 3 : Tri et limitation (`sort`, `limit`)

```python
# 3. Les 10 produits les plus chers, triés par prix décroissant
q3 = products.find().sort("price", DESCENDING).limit(10)
print("Q3 - Top 10 prix décroissant :")
for p in q3:
    print(" -", p["name"], p["price"])
```
- `.sort("price", DESCENDING)` : Trie les résultats par prix du plus élevé au plus bas.
- `.limit(10)` : Restreint le résultat aux 10 premiers documents (le "Top 10").

---

## 5. Requête 4 : Pagination robuste (`skip`, `limit`, tri composite)

```python
# 4. Pagination : page 3 avec 20 produits par page, triés par nom
#    (tri secondaire sur _id pour un ordre déterministe en cas de noms
#    identiques — sans ça, skip/limit n'est pas garanti stable)
page = 3
page_size = 20
q4 = (
    products.find()
    .sort([("name", ASCENDING), ("_id", ASCENDING)])
    .skip((page - 1) * page_size)
    .limit(page_size)
)
resultats_q4 = list(q4)
print(f"Q4 - Page {page} ({page_size} résultats/page), {len(resultats_q4)} trouvés :")
for p in resultats_q4:
    print(" -", p["name"], p["price"])
```
- `page = 3` et `page_size = 20` : Paramètres de pagination.
- `.sort([("name", ASCENDING), ("_id", ASCENDING)])` : Tri composite. Le tri secondaire sur `_id` garantit un ordre déterministe (stable) même si plusieurs produits ont exactement le même nom.
- `.skip((page - 1) * page_size)` : Ignore les `40` premiers documents (`(3 - 1) * 20`) pour atteindre la 3ème page.
- `.limit(page_size)` : Récupère uniquement les 20 documents de la page courante.
- `list(q4)` : Convertit le curseur MongoDB en liste Python concrète.

---

## 6. Requête 5 : Filtre combiné et tri

```python
# 5. Produits en rupture de stock (stock = 0) d'une catégorie donnée, triés par prix croissant
q5 = products.find({"category": "informatique", "stock": 0}).sort("price", ASCENDING)
resultats_q5 = list(q5)
print(f"Q5 - Rupture stock informatique, {len(resultats_q5)} trouvé(s) :")
for p in resultats_q5:
    print(" -", p["name"], p["price"], "(stock:", p["stock"], ")")
```
- `{"category": "informatique", "stock": 0}` : Filtre combiné (ET implicite) recherchant les produits informatiques ayant un stock égal à 0.
- `.sort("price", ASCENDING)` : Trie les ruptures de stock obtenues par prix croissant.
