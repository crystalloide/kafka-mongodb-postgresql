# Explication détaillée du script : rebalance_consumer.py

Ce document détaille le code source du script Python illustrant l'utilisation d'un consommateur Kafka (`KafkaConsumer`) associé à un `ConsumerRebalanceListener` pour intercepter et logger les événements de rééquilibrage des partitions (`rebalance`).

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
import json
import os
from typing import Collection

from dotenv import load_dotenv
from kafka import KafkaConsumer, ConsumerRebalanceListener, TopicPartition

load_dotenv()
```
- Importe les classes Kafka nécessaires, notamment `ConsumerRebalanceListener` pour gérer les callbacks de rééquilibrage et `TopicPartition` pour manipuler les partitions.

### 2. Paramètres de connexion et identification du groupe
```python
BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"
```
- Configure les serveurs bootstrap, le topic cible et le `group_id` du groupe de consommateurs.

### 3. Définition du Listener de rééquilibrage (`RebalanceLogger`)
```python
class RebalanceLogger(ConsumerRebalanceListener):
    \"\"\"Listener pour afficher les partitions révoquées/assignées.\"\"\"

    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer

    def on_partitions_revoked(self, revoked: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions révoquées :", list(revoked))

    def on_partitions_assigned(self, assigned: Collection[TopicPartition]) -> None:
        print("[REBALANCE] Partitions assignées :", list(assigned))
```
- Hérite de `ConsumerRebalanceListener` pour observer le cycle de vie du groupe de consommateurs :
  - `on_partitions_revoked`: Déclenché lorsqu'un rééquilibrage est initié et que des partitions sont retirées au consommateur (souvent l'occasion de faire un commit manuel des offsets en cours).
  - `on_partitions_assigned`: Déclenché lorsque de nouvelles partitions sont attribuées au consommateur après la fin du rééquilibrage.

### 4. Initialisation du consommateur et abonnement
```python
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
```
- Initialise le consommateur en mode groupe (`group_id`) avec désérialisation automatique de la clé en chaîne et de la valeur en dictionnaire JSON.
- `auto_offset_reset="earliest"`: Lit depuis le début si aucun offset n'est enregistré.
- `consumer.subscribe([TOPIC], listener=listener)`: S'abonne au topic en enregistrant le listener personnalisé pour tracer les rééquilibrages.

### 5. Boucle de consommation et gestion des interruptions
```python
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
- Parcourt les messages reçus en continu, affiche les métadonnées de partition, offset, clé ainsi que l'identifiant de commande extrait du payload JSON.
- Capture `KeyboardInterrupt` (`Ctrl+C`) pour arrêter proprement le consommateur et libérer les ressources avec `consumer.close()`.
