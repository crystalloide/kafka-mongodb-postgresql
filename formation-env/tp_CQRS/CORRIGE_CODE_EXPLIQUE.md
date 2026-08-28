# Guide formateur — lecture des scripts de la solution

## `command_api.py`

Le point clé est la transaction PostgreSQL. La création de la commande, des lignes et de l'événement Outbox se trouve dans le même bloc de connexion transactionnel.

Le programme ne parle plus directement à Kafka. Il persiste un événement `OrderCreated` dans `outbox_events` et retourne ensuite la réponse HTTP.

Lors de l'annulation, PostgreSQL vérifie l'état courant et incrémente `orders.version`. L'événement `OrderCancelled` porte la nouvelle version.

## `outbox_publisher.py`

Le publisher recherche les événements dont `published_at` est NULL, les envoie à Kafka avec `aggregate_id` comme clé, attend la confirmation, puis renseigne `published_at`.

Une panne après l'envoi mais avant le commit PostgreSQL peut provoquer un doublon. C'est volontaire et sert à introduire l'idempotence du Projector.

## `projector.py`

Le Projector lit `aggregate_version`. Si la version reçue est inférieure ou égale à `last_event_version`, l'événement est ignoré.

Ce mécanisme protège à la fois contre les doublons et contre un événement ancien qui arriverait après un événement plus récent.

Le cas d'une annulation comme premier événement est géré en créant une vue minimale `CANCELLED`. Dans le scénario normal, `OrderCreated` version 1 précède `OrderCancelled` version 2.

## `query_api.py`

La Query API ne connaît pas PostgreSQL. Elle ne lit que MongoDB `orders_view`. Cette ignorance volontaire du Write Model matérialise la séparation CQRS.
