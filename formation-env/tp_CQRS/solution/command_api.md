# Explication — Command API de la solution

La Command API reçoit les commandes HTTP. Elle valide les données, applique les premières règles métier et écrit dans PostgreSQL.

La création est transactionnelle : `orders`, `order_items` et `outbox_events` sont validés ensemble. L'API ne publie pas directement dans Kafka.

L'événement Outbox contient notamment `event_id`, `event_type`, `occurred_at`, `aggregate_version` et `payload`.

La commande d'annulation vérifie l'état de l'ordre dans PostgreSQL. Une commande déjà annulée entraîne HTTP 409.
