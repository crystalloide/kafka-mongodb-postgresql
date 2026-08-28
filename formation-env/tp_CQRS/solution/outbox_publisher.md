# Explication — Outbox Publisher

`outbox_publisher.py` sépare la transaction métier de la publication Kafka.

Il interroge PostgreSQL pour trouver les événements non publiés, publie leur `payload` dans `orders.events` avec `aggregate_id` comme clé Kafka, attend la confirmation du broker, puis renseigne `published_at`.

Ce mécanisme garantit que l'événement est conservé dans PostgreSQL tant qu'il n'a pas été publié avec succès. Il ne garantit pas exactement une fois : un crash après publication et avant le marquage peut provoquer une nouvelle publication.
