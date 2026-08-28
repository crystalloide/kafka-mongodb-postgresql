# Solution complète

Cette version correspond à l'architecture CQRS proposée :

- PostgreSQL : Write Model et Transactional Outbox
- `command_api.py` : Command API + logique de commande
- `outbox_publisher.py` : publication Outbox -> Kafka
- Kafka : transport des événements `orders.events`
- `projector.py` : projection idempotente Kafka -> MongoDB
- MongoDB : Read Model `training.orders_view`
- `query_api.py` : Query API

La solution privilégie la simplicité pédagogique. L'Outbox fournit une garantie de type at-least-once vers Kafka : un crash entre la publication Kafka et le marquage `published_at` peut produire un doublon. Le projecteur est donc conçu pour être idempotent grâce à `aggregate_version`.
