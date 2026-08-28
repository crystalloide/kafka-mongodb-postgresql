# Explication détaillée du script : projector.py 

Ce document détaille le code source du script Python implémentant un **Projecteur** (CQRS / Event Sourcing) . Il écoute les événements Kafka (`orders.events`), détecte automatiquement si la vue MongoDB est vide pour rejouer l'historique complet, et met à jour une vue matérialisée (`orders_view`) .

Le topic Kafka joue ici le rôle de **journal d'événements**.

Pour être précis et rigoureux, nous avons ici un **projecteur CQRS basé sur un journal d'événements Kafka** ou encore **Projecteur CQRS dans une architecture de type Event Sourcing**

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
import json
import os
import uuid
from typing import Any
from dotenv import load_dotenv
from kafka import KafkaConsumer
from pymongo import MongoClient

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092,localhost:9094,localhost:9096").split(",")
ORDERS_EVENTS_TOPIC = "orders.events"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://formation:formation@localhost:27017/?authSource=admin&replicaSet=rs0")
```
- Importe les modules standards (`json`, `os`, `uuid`, `Any`), le client Kafka (`KafkaConsumer`), et le client MongoDB (`MongoClient`) .
- Charge les variables d'environnement (`load_dotenv`) et configure les paramètres de connexion Kafka et MongoDB avec des valeurs par défaut .

### 2. Connexion à MongoDB et initialisation de la vue
```python
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["training"]
orders_view = db["orders_view"]

# 1. Auto-détection de l'état de la base de données
is_empty = orders_view.count_documents({}) == 0

# 2. Assignation dynamique du groupe Kafka
if is_empty:
    # Base vide = nouveau groupe pour forcer la relecture de tout l'historique
    GROUP_ID = f"orders-projector-group-rebuild-{uuid.uuid4()}"
    print("🔄 Vue MongoDB vide détectée ! Rejeu automatique de l'historique en cours...")
else:
    # Base existante = on reprend la lecture normale
    GROUP_ID = "orders-projector-group"
    print("✅ Vue MongoDB existante. Reprise de la lecture classique...")
```
- Se connecte à la base `training` et cible la collection de vue matérialisée `orders_view` .
- Vérifie si la vue est vide (`count_documents({}) == 0`) .
- Si la vue est vide, génère dynamiquement un `GROUP_ID` unique (`uuid.uuid4()`) pour forcer Kafka à repartir du début (`earliest`) et reconstruire tout l'historique des événements . Sinon, utilise le groupe standard `orders-projector-group` pour une reprise normale . **Précision importante :** Si le groupe est nouveau, **auto_offset_reset="earliest"** demande de commencer au plus ancien offset encore disponible dans le topic afin de reconstruire la vue. ``earliest`` signifie : commencer au plus ancien offset disponible pour ce groupe, pas nécessairement au premier événement historique jamais produit. En effet, si certains anciens événements ont déjà été supprimés par la politique de rétention Kafka ( exemple ! 7 jours de rétention par défaut) , ils ne seront évidemment pas relus. Kafka définit **earliest** précisément comme le plus ancien offset disponible lorsqu'il n'existe pas d'offset initial.

### 3. Initialisation du KafkaConsumer
```python
consumer = KafkaConsumer(
    ORDERS_EVENTS_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)
```
- Initialise le consommateur Kafka abonné à `orders.events` avec désérialisation JSON
- `auto_offset_reset="earliest"` signifie qu'on démarre au plus ancien offset disponible dans le topic
- `enable_auto_commit=True` signifie une validation automatique des offsets : il peut exister une situation où l'offset est considéré comme consommé alors que la mise à jour MongoDB n'est pas correctement finalisée : ``at most once`` dans ce cas. En utilisant un commit explicite, on pourrait alors se retrouver dans l'autre situation de ``at least once`` et des risques de "pilule empoisonnée" si un message ne peut être traité et que le code ne gère pas bien cette situation. 

### 4. Fonctions de projection des événements
```python
def apply_order_created(event: dict[str, Any]) -> None:
    payload = event["payload"]
    order_id = payload["order_id"]
    doc = {
        "order_id": order_id,
        "customer_id": payload["customer_id"],
        "status": "CREATED",
        "items": payload["items"],
        "total_amount": payload["total_amount"],
        "last_event_id": event["event_id"],
        "last_event_at": event["occurred_at"],
    }
    orders_view.update_one({"order_id": order_id}, {"$set": doc}, upsert=True)

def apply_order_cancelled(event: dict[str, Any]) -> None:
    payload = event["payload"]
    orders_view.update_one(
        {"order_id": payload["order_id"]},
        {"$set": {"status": "CANCELLED", "last_event_id": event["event_id"], "last_event_at": event["occurred_at"]}},
        upsert=True,
    )
```
- `apply_order_created`: Traite l'événement `OrderCreated` en créant ou mettant à jour un document de synthèse dans `orders_view` avec le statut `"CREATED"`, les articles et le montant total .
- `apply_order_cancelled`: Traite l'événement `OrderCancelled` en basculant le statut de la commande à `"CANCELLED"` dans MongoDB .
- L'utilisation de `upsert=True` permet de traiter même si l'événement d'annulation arrive avant la création (ou en cas de rejeu partiel). Attention, il ne garantit pas à lui seul la cohérence de l'ordre des événements : un **OrderCreated** traité après un **OrderCancelled** pourrait ainsi remettre le statut à **CREATED**. C'est un point particulièrement intéressant pour expliquer pourquoi l'ordre des événements et la logique d'idempotence/versionnement sont importants dans un projecteur.

### 5. Boucle principale d'écoute
```python
if __name__ == "__main__":
    print("Projecteur en écoute active... Ctrl+C pour arrêter.")
    try:
        for msg in consumer:
            event = msg.value
            event_type = event.get("event_type")
            if event_type == "OrderCreated":
                apply_order_created(event)
            elif event_type == "OrderCancelled":
                apply_order_cancelled(event)
    except KeyboardInterrupt:
        pass
    finally:
        mongo_client.close()
        consumer.close()
```
- Itère en continu sur les messages Kafka, identifie le type d'événement (`event_type`) et applique la fonction de projection correspondante .
- Ferme proprement les connexions MongoDB et Kafka lors de l'arrêt .
