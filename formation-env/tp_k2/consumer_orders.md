# Explication détaillée du script : consumer_orders.py

Ce document détaille le code source du script Python illustrant un consommateur Kafka classique (`KafkaConsumer`) écoutant un topic et traitant les événements de commandes en temps réel.

---

## Explication ligne par ligne et bloc par bloc

### 1. Importations et configuration initiale
```python
import json
import os

from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()
```
- Importe les modules standards et `KafkaConsumer` pour recevoir les messages des topics Kafka.

### 2. Configuration des paramètres Kafka
```python
BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP",
    "localhost:9092,localhost:9094,localhost:9096",
).split(",")

TOPIC = "orders.events"
GROUP_ID = "orders-events-group"
```
- Définit les serveurs bootstrap, le nom du topic à écouter (`orders.events`) et l'identifiant du groupe de consommateurs (`orders-events-group`).

### 3. Initialisation du KafkaConsumer
```python
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",  # lire depuis le début si aucun offset
    enable_auto_commit=True,        # commit automatique des offsets
)
```
- Passe directement le topic à écouter lors de l'instanciation.
- `key_deserializer` et `value_deserializer`: Convertissent automatiquement les octets reçus en chaînes de caractères et dictionnaires Python (JSON).
- `auto_offset_reset="earliest"`: Positionne le curseur au début du topic s'il n'y a pas d'offset stocké pour ce groupe.
- `enable_auto_commit=True`: Valide automatiquement les offsets de manière périodique.

### 4. Boucle de lecture et traitement des messages
```python
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
- `for msg in consumer:`: Itérateur bloquant qui attend et récupère les nouveaux messages en temps réel.
- Extrait les informations clés du message (`partition`, `offset`, `key`) et les détails métier du payload (`event_type`, `order_id`, `customer_id`, `total_amount`).
- Assure une fermeture propre du consommateur lors de l'interruption utilisateur (`Ctrl+C`).
