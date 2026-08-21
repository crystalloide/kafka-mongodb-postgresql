## TP M2 — Modélisation de documents & agrégation - Réponse aux questions


### 1°) Questions posées : **0. Rappel — Modèle embarqué vs référencé**

- Dans quels cas le modèle embarqué est-il plus simple et plus performant ?
- Quand le modèle référencé devient-il nécessaire (taille des documents, réutilisation des lignes de commande, besoins d'agrégation avancés) ?
- Quel modèle est le plus adapté à une vue de lecture CQRS où l'on veut répondre rapidement à des requêtes comme « commandes d'un client sur une période » ?


---

#### 1. Dans quels cas le modèle embarqué est-il plus simple et plus performant ?

Le modèle embarqué est optimal quand on retrouve le principe **« les données consultées ensemble doivent être stockées ensemble »** :

- **Relation 1-à-few bornée** : une commande a rarement plus de quelques dizaines de lignes ; le tableau `items` reste petit et loin de la limite BSON de 16 Mo par document.
- **Lecture atomique** : une seule requête `find()` renvoie la commande complète avec ses lignes, sans `$lookup` ni round-trip supplémentaire.
- **Atomicité des écritures** : MongoDB garantit l'atomicité au niveau du document — modifier une commande et ses lignes en une seule opération est naturel avec l'embarqué (ex. annuler une commande et recalculer son total).
- **Pas de réutilisation des sous-documents** : les `items` d'une commande n'ont de sens que dans le contexte de *cette* commande (un même libellé produit répété dans deux commandes n'est pas un problème puisqu'il n'y a pas de relation à maintenir entre les deux occurrences).

C'est exactement le cas du TP : chaque commande a 1 à 5 items, jamais consultés indépendamment de leur commande.

---

#### 2. Quand le modèle référencé devient-il nécessaire ?

Trois signaux typiques :

- **Taille/croissance non bornée** : si le tableau peut grossir indéfiniment (ex. un panier qui accumule des événements sur des années, un historique de logs par commande), le risque de dépasser 16 Mo — ou simplement de dégrader les performances de lecture/écriture d'un document trop gros — pousse vers une collection séparée.
- **Réutilisation / partage** : si les « lignes » référencent une entité qui existe indépendamment et doit rester cohérente à plusieurs endroits (ex. un catalogue produit avec prix mis à jour centralement, référencé par des milliers de commandes), embarquer forcerait à dupliquer et à ne plus pouvoir mettre à jour un produit sans parcourir toutes les commandes qui le contiennent.
- **Agrégations ou requêtes centrées sur les lignes elles-mêmes** : si on doit fréquemment interroger, indexer ou agréger les lignes indépendamment de leur commande parente (ex. « quelles sont les lignes avec la plus forte marge, toutes commandes confondues », mises à jour unitaires fréquentes d'une ligne sans toucher au reste de la commande), une collection `order_lines` dédiée, indexable indépendamment, devient plus efficace qu'un `$unwind` systématique.

---

#### 3. Quel modèle pour une vue de lecture CQRS « commandes d'un client sur une période » ?

**Le modèle embarqué est le plus adapté ici**, et c'est un bon point de bascule pédagogique vers la partie CQRS de la formation :

- Le besoin exprimé est une lecture **dénormalisée et rapide**, exactement ce que vise une vue de lecture CQRS : on veut restituer une commande complète (items compris) sans jointure au moment de la requête.
- Avec le modèle embarqué, `db.orders.find({customer_id, order_date: {$gte: ..., $lte: ...}})` (avec un index composé `{customer_id: 1, order_date: -1}`) suffit à répondre en une seule opération.
- Avec le modèle référencé, il faudrait soit un `$lookup` (coûteux à grande échelle, comme le souligne la synthèse du TP), soit deux requêtes applicatives — ce qui va à l'encontre de l'objectif de latence faible d'une vue de lecture.

**Point clé à faire ressortir avec les stagiaires** : le modèle de la vue de lecture n'a pas à être le même que celui du modèle d'écriture/domaine. En CQRS, on peut très bien avoir un modèle référencé côté « source de vérité » (write side) et projeter, via les événements, une vue matérialisée embarquée et dénormalisée côté lecture — c'est précisément le rôle des projections dans un système Event Sourcing + CQRS.

---

#### En synthèse :

| Critère | Embarqué | Référencé |
|---|---|---|
| Lecture complète en 1 requête | ✅ | ❌ (nécessite `$lookup`) |
| Taille/croissance illimitée | ❌ risque 16 Mo | ✅ |
| Réutilisation d'une entité entre documents | ❌ duplication | ✅ |
| Mise à jour atomique commande+lignes | ✅ | ❌ (2 écritures) |
| Adapté aux vues de lecture CQRS | ✅ | ⚠️ à éviter en lecture directe |


---


### 2°) Question posées concernant le Pipeline d'agrégation (CA par client et par mois) 

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


#### Questions pour les stagiaires

- Que se passe-t-il si l'on **supprime** l'étape `$unwind` du pipeline ? Les résultats sont-ils encore cohérents ?
- Comment filtrer uniquement les clients du segment `"gold"` dans ce pipeline ? (Indice : ajouter un `$match` après le `$lookup` sur `customers`.)
- Comment adapter ce pipeline pour calculer le CA **par mois uniquement**, sans détail par client (changer les clés du `$group`).



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

1. **Modèle embarqué** ou **embedded** : toutes les lignes de commande sont stockées dans un tableau `items` à l'intérieur du document `orders`.
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

Objectif : 
- créer un jeu de données réaliste avec des clients et des commandes, en utilisant Faker. 
- Les commandes utiliseront le **modèle embarqué** avec un tableau `items`.

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
use training;
```

```scriptMongosh
db.customers.find().limit(5).pretty();
```

```scriptMongosh
db.orders.find().limit(5).pretty();
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

### Questions posées :

#### 1. Que se passe-t-il si l'on **supprime** l'étape `$unwind` du pipeline ? Les résultats sont-ils encore cohérents ?

Suppression du $unwind

Le pipeline échoue avec une erreur d'exécution, il ne produit pas simplement des résultats faux.

Sans $unwind, **items** reste un tableau de sous-documents au moment du $group. Dans une expression d'agrégation, accéder à $items.unit_price sur un champ tableau ne renvoie pas une valeur scalaire mais un tableau de valeurs (une par élément d'items) — idem pour $items.quantity. Or $multiply exige des opérandes numériques : on obtiendrait une erreur du type

**$multiply only supports numeric types, not array**

et ce même si chaque commande n'a qu'une seule ligne (un tableau à un seul élément reste un tableau, MongoDB ne le "déballe" pas automatiquement).

C'est exactement l'intérêt pédagogique de cette question : $unwind transforme chaque document commande (avec son tableau items) en autant de documents qu'il y a de lignes, chacun portant un items scalaire (objet unique, plus tableau). C'est ce qui rend $items.unit_price et $items.quantity accessibles comme des nombres simples pour $multiply. Sans cette étape, le modèle embarqué n'est pas "aplati" et le calcul ligne à ligne est impossible tel quel.

Remarque annexe (pour aller plus loin avec les stagiaires) : on pourrait calculer un total par commande sans $unwind, mais il faudrait alors sommer le tableau explicitement, par exemple avec $sum sur un $map :

```python
"order_total": {
    "$sum": {
        "$map": {
            "input": "$items",
            "as": "it",
            "in": {"$multiply": ["$$it.unit_price", "$$it.quantity"]}
        }
    }
}
```

Mais cela changerait la granularité du pipeline (un total par commande, pas par ligne), ce qui n'est pas ce qui est demandé.


#### 2. Comment filtrer uniquement les clients du segment `"gold"` dans ce pipeline ? 

L'Indice donné était d'ajouter un `$match` après le `$lookup` sur `customers` :

On insère un $match après le $unwind: "$customer", une fois que la jointure a été aplatie en un sous-document unique (plus simple à filtrer qu'un tableau) :

```python
{
    "$lookup": {
        "from": "customers",
        "localField": "_id.customer_id",
        "foreignField": "_id",
        "as": "customer",
    }
},
{"$unwind": "$customer"},
{"$match": {"customer.segment": "gold"}},   # <-- nouvelle étape
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
```

**Remarque :**

Ce filtre s'applique après le calcul du CA (donc après $group), ce qui est correct ici puisqu'on ne fait que restreindre l'affichage aux clients "gold" : 
- Le CA de chaque ligne reste calculé sur les commandes de ce client uniquement, donc rien n'est faussé. 

On pourrait aussi filtrer plus tôt (avant $group, avec un premier $lookup sur customers), mais ce serait moins efficace : 
- on ferait la jointure et le filtrage segment avant d'avoir réduit les données via $group, donc sur un volume de lignes plus important (une ligne par item au lieu d'une ligne par client/mois).


#### 3.- Comment adapter ce pipeline pour calculer le CA **par mois uniquement**, sans détail par client (changer les clés du `$group`).

Calcul du CA par mois uniquement (sans détail client)

Il suffit de :
- retirer **customer_id** de la clé _id du $group
- et de supprimer ce qui dépend du client ($lookup, $unwind customer, customer_name dans $project)

```python
pipeline = [
    {"$match": {"status": "CONFIRMED"}},
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": {
                "year": {"$year": "$order_date"},
                "month": {"$month": "$order_date"},
            },
            "revenue": {
                "$sum": {"$multiply": ["$items.unit_price", "$items.quantity"]}
            },
        }
    },
    {
        "$project": {
            "_id": 0,
            "year": "$_id.year",
            "month": "$_id.month",
            "revenue": 1,
        }
    },
    {"$sort": {"year": 1, "month": 1}},
]
```

Le $lookup/$unwind sur customers disparaît entièrement puisqu'on n'a plus besoin du nom du client. 

**Remarque :** 

La clé du $group définit directement le niveau de granularité du résultat : 
- moins de clés dans _id = plus d'agrégation (ici, toutes les lignes de tous les clients d'un même mois sont fusionnées en une seule ligne de résultat).
  
---



