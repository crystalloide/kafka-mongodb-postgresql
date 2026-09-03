## TP K2 — Producteur/Consommateur avec kafka-python 2.3.1

**Durée** : 60 min

**Prérequis** :
- TP K1 réalisé (topics `orders.commands` et `orders.events` créés avec 3 partitions, RF=3, `min.insync.replicas=2`).
- Environnement Docker Compose démarré (Kafka 3.8.1 KRaft, Kafka UI, Kafka Connect, PostgreSQL, MongoDB).
- venv Python activé, dépendances installées (`kafka-python==2.3.1`, `python-dotenv`).
- Fichier `.env` avec `KAFKA_BOOTSTRAP` (liste des brokers host) et `MONGO_URI` configurés.

## Objectifs

- Utiliser `KafkaProducer` (kafka-python 2.3.1) avec sérialisation JSON, clé de partitionnement, `acks='all'` et callbacks de succès/erreur.
- Utiliser `KafkaConsumer` avec groupes de consommateurs, `auto_offset_reset`, commit manuel vs automatique, désérialisation JSON.
- Mettre en place un producteur qui publie des événements `OrderCreated` sur `orders.events`.
- Mettre en place deux consommateurs dans le même groupe pour observer le **rééquilibrage des partitions** via un `ConsumerRebalanceListener`.

---

## 00. Rappel des topics et de la configuration Kafka (5 min)

Avant de commencer :

- Les topics ont été créés au TP K1 :
  - `orders.commands` : 3 partitions, RF=3.
  - `orders.events` : 3 partitions, RF=3, `min.insync.replicas=2`.
- `KAFKA_BOOTSTRAP` dans le `.env` pointe vers les brokers host de formation :

```text
KAFKA_BOOTSTRAP=localhost:9092,localhost:9094,localhost:9096
```

Ce TP utilisera le topic `orders.events` pour publier des événements de type `OrderCreated`.

---

## 0. Nouveau terminal :

Dans un nouveau terminal :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```
### Pré-requis

###  0. Préparation VS Code & environnement Python (30 min, transverse)

Objectif : chaque stagiaire a un environnement fonctionnel avant de commencer les TP techniques.

- Vérifier que tous les conteneurs sont `Up (healthy)` :
```bash
su - user
```

```bash
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

- Fichier `requirements.txt` à (re)créer si non présent/renseigné :
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
flask
fastapi
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


```bash
cd tp_k2
```


## 1. Producteur — `KafkaProducer` avec JSON et `acks='all'` (20 min)

Objectif : créer un producteur Python qui envoie des événements `OrderCreated` en JSON sur `orders.events` avec des garanties de durabilité fortes (`acks='all'`).

### 1.1 Code du producteur `producer_orders.py`

Créez le fichier `producer_orders.py` :

```python
import json
import os
from uuid import uuid4
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",  # attente de l'ack de tous les ISR (durabilité forte)
)


def on_send_success(record_metadata):
    print(
        f"[SUCCESS] topic={record_metadata.topic} "
        f"partition={record_metadata.partition} offset={record_metadata.offset}"
    )


def on_send_error(ex):
    print(f"[ERROR] envoi sur {TOPIC} : {ex}")


def build_order_created(customer_id: str, items: list[dict]) -> dict:
    """Construit un événement OrderCreated en JSON.

    items: liste de dicts {"product_id", "quantity", "unit_price"}.
    """
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

### 1.2 Points pédagogiques

- `key_serializer` / `value_serializer` : sérialisation de la clé (string) et de la valeur (JSON) en bytes.
- `acks="all"` : le producteur attend l’ack du leader **et de toutes les ISR** avant de considérer l’écriture réussie.
- Callbacks `on_send_success` / `on_send_error` : permettent d’observer le chemin de succès/échec.
- Clé de partitionnement (`customer_id`) : garantit que toutes les commandes d’un même client vont sur la même partition, donc conservent l’ordre.

---

## 2. Consommateur — `KafkaConsumer` avec groupe et commit (20 min)

Objectif : créer un consommateur Python qui lit les événements `OrderCreated` depuis `orders.events` en utilisant un **groupe de consommateurs** Kafka.

### 2.1 Code du consommateur `consumer_orders.py`

Créez le fichier `consumer_orders.py` :

```python
import json
import os

from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",  # lire depuis le début si aucun offset
    enable_auto_commit=True,        # commit automatique des offsets
)

print(
    f"Consommateur démarré sur topic={TOPIC}, group_id={GROUP_ID}. "
    "Ctrl+C pour arrêter."
)

try:
    for msg in consumer:
        key = msg.key
        event = msg.value
        partition = msg.partition
        offset = msg.offset

        print(
            f"[EVENT] partition={partition} offset={offset} key={key}\n"
            f"        event_type={event['event_type']} "
            f"order_id={event['payload']['order_id']} "
            f"customer_id={event['payload']['customer_id']} "
            f"total={event['payload']['total_amount']}"
        )

except KeyboardInterrupt:
    print("\nArrêt du consommateur.")
finally:
    consumer.close()
```

### 2.2 Points pédagogiques

- `group_id` : les consommateurs partageant le même `group_id` se répartissent les partitions du topic.
- `auto_offset_reset="earliest"` : comportement lorsqu’il n’y a pas d’offset existant pour ce groupe.
- `enable_auto_commit=True` : Kafka gère les commits d’offsets; tu pourras montrer plus tard le commit manuel.

---

## 3. Rééquilibrage des partitions avec `ConsumerRebalanceListener` (20 min)

Objectif : lancer **deux instances** du consommateur dans le même groupe et observer le rééquilibrage des partitions (rebalancing) à l’ajout/retrait d’un consommateur.

### 3.1 Consommateur avec listener `rebalance_consumer.py`

Créez le fichier `rebalance_consumer.py` :

```python
import json
import os
from typing import Collection

from dotenv import load_dotenv
from kafka import KafkaConsumer, ConsumerRebalanceListener, TopicPartition

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"


class RebalanceLogger(ConsumerRebalanceListener):
    """Listener pour afficher les partitions révoquées/assignées."""

    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer

    def on_partitions_revoked(self, revoked: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions révoquées :", list(revoked))

    def on_partitions_assigned(self, assigned: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions assignées :", list(assigned))


consumer = KafkaConsumer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

listener = RebalanceLogger(consumer)

consumer.subscribe([TOPIC], listener=listener)

print(
    f"Consommateur avec listener démarré sur topic={TOPIC}, group_id={GROUP_ID}. "
    "Ctrl+C pour arrêter."
)

try:
    for msg in consumer:
        key = msg.key
        event = msg.value
        partition = msg.partition
        offset = msg.offset

        print(
            f"[EVENT] partition={partition} offset={offset} key={key} "
            f"order_id={event['payload']['order_id']}"
        )

except KeyboardInterrupt:
    print("\nArrêt du consommateur.")
finally:
    consumer.close()
```

### 3.2 Scénario d’exécution pour observer le rééquilibrage

1. Lancer le **producteur** une première fois pour générer des événements :

```bash
python producer_orders.py
```

2. Ouvrir une nouvelle console et lancer le 1er consommateur avec listener :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
cd tp_k2
```

```bash
python rebalance_consumer.py
```

   - Notez les partitions assignées (par exemple `[orders.events-0, orders.events-1, orders.events-2]`).

3. Ouvrir encore un autre terminal et lancer une **seconde instance** de `rebalance_consumer.py` avec le même `group_id` :

Dans un nouveau terminal :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
cd tp_k2
```

```bash
python rebalance_consumer.py
```

   - Observez les logs `[REBALANCE]` dans les deux consoles : les partitions sont réparties entre les deux consommateurs.
   - Chaque consommateur ne reçoit qu’une **partie** des événements, en fonction de ses partitions.

4. Arrêtez l’une des instances ( = Faire Ctrl+C dans un des 2 précédents terminaux) :
   - Observez un nouveau rebalancing : les partitions reviennent au consommateur restant.

### Points pédagogiques

- Le **groupe de consommateurs** Kafka garantit que chaque événement est traité par **un seul** consommateur du groupe.
- Les partitions sont redistribuées automatiquement lorsque des consommateurs rejoignent ou quittent le groupe.
- `ConsumerRebalanceListener` permet de tracer ces changements et de gérer des actions applicatives (commit manuel, nettoyage d’état, etc.).

---

## 4. Synthèse pédagogique

- `KafkaProducer` avec `acks='all'` et clé de partitionnement permet de contrôler durabilité et ordre des messages.
- `KafkaConsumer` en groupe et avec listener de rebalancing illustre le partage de charge et la résilience.
- Les événements `OrderCreated` sur `orders.events` serviront de base aux TPs suivants (Kafka Connect, CQRS) pour alimenter des projections et des pipelines de données.
