# Explication — Projector

Le Projector consomme `orders.events` et construit `training.orders_view`.

Il utilise `aggregate_version` pour rendre la projection idempotente. Un événement dont la version est inférieure ou égale à `last_event_version` est ignoré.

`OrderCreated` matérialise les articles et le montant total. `OrderCancelled` modifie le statut et les métadonnées du dernier événement.

Si `orders_view` est vide, un nouveau groupe Kafka est créé avec `auto_offset_reset="earliest"` : la lecture commence au plus ancien offset encore disponible.
