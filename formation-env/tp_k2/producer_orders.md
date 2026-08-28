# Explication détaillée du script : producer_orders.py

Ce document détaille le code source du script Python simulant un producteur Kafka (`KafkaProducer`) qui génère et envoie des événements de création de commandes (`OrderCreated`) vers un topic Kafka avec une durabilité forte (`acks="all"`) et un partitionnement par clé client.

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
import json
import os
from uuid import uuid4
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()
```
- `json`: Pour sérialiser les dictionnaires Python en chaînes JSON.
- `uuid4`: Pour générer des identifiants uniques universels (UUID v4) pour les événements et les commandes.
- `datetime`: Pour hordater précisément les événements.
- `load_dotenv()`: Charge les variables d'environnement depuis le fichier `.env`.
- `KafkaProducer`: Classe du client Kafka pour publier des messages.

### 2. Configuration des serveurs Bootstrap et du Topic
```python
BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
```
- Récupère la liste des brokers Kafka depuis l'environnement (ou utilise une valeur par défaut multi-broker) et la sépare en liste.
- Définit le nom du topic cible : `orders.events`.

### 3. Initialisation du KafkaProducer
```python
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",  # attente de l'ack de tous les ISR (durabilité forte)
)
```
- `bootstrap_servers`: Les serveurs de connexion Kafka.
- `key_serializer`: Fonction convertissant la clé du message (ex: `customer_id`) en octets (`utf-8`).
- `value_serializer`: Fonction convertissant l'objet dictionnaire de l'événement en une chaîne JSON puis en octets (`utf-8`).
- `acks="all"`: Garantit une durabilité maximale en exigeant que le leader et tous les réplicas synchronisés (`ISR` - In-Sync Replicas) acquittent l'écriture avant de valider le succès.

### 4. Callbacks de succès et d'erreur
```python
def on_send_success(record_metadata):
    print(
        f"[SUCCESS] topic={record_metadata.topic} "
        f"partition={record_metadata.partition} offset={record_metadata.offset}"
    )


def on_send_error(ex):
    print(f"[ERROR] envoi sur {TOPIC} : {ex}")
```
- `on_send_success`: Callback exécuté en cas de succès, affichant le topic, la partition et l'offset assigné.
- `on_send_error`: Callback exécuté en cas d'échec de l'envoi asynchrone.

### 5. Fonction de construction d'événement (`build_order_created`)
```python
def build_order_created(customer_id: str, items: list[dict]) -> dict:
    \"\"\"Construit un événement OrderCreated en JSON.

    items: liste de dicts {\"product_id\", \"quantity\", \"unit_price\"}.
    \"\"\"
    return {
        "event_id": str(uuid4()),
        "event_type": "OrderCreated",
        "occurred_at": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "order_id": str(uuid4()),
            "customer_id": customer_id,
            "items": items,
            "total_amount": sum(
                i["quantity"] * i["unit_price"] for i in items
            ),
        },
    }
```
- Structure l'événement selon un format standardisé orienté domaine (DDD / Event-Driven Architecture) : identifiant d'événement, type d'événement (`OrderCreated`), horodatage UTC et un `payload` contenant les détails de la commande et le calcul automatique du montant total.

### 6. Boucle d'envoi principal
```python
if __name__ == "__main__":
    print(f"Envoi de 10 événements OrderCreated sur {TOPIC}...")

    for i in range(10):
        customer_id = f"CUST-{1000 + i}"
        items = [
            {"product_id": "P-001", "quantity": 1, "unit_price": 79.9},
            {"product_id": "P-002", "quantity": 2, "unit_price": 29.9},
        ]
        event = build_order_created(customer_id, items)

        # Clé de partitionnement = customer_id pour conserver l'ordre
        future = producer.send(TOPIC, key=customer_id, value=event)
        future.add_callback(on_send_success)
        future.add_errback(on_send_error)

    # Flush pour s'assurer que tout est envoyé
    producer.flush()
    producer.close()

    print("Terminé.")
```
- Boucle pour générer et envoyer 10 événements.
- `producer.send(TOPIC, key=customer_id, value=event)`: Envoie l'événement de manière asynchrone. L'utilisation de `customer_id` comme clé garantit que tous les messages d'un même client aboutissent dans la même partition (garantie d'ordre par client).
- `producer.flush()`: Force l'envoi de tous les messages en attente dans le buffer avant de fermer le producteur.
