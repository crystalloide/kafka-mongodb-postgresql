# Correction — TP CQRS PostgreSQL + Kafka + MongoDB

## Exercice 1

1. Dans le système initial, la commande n'est pas persistée dans une base d'écriture par la Command API : elle est transformée en événement et envoyée directement à Kafka.
2. `projector.py` écrit dans `training.orders_view`.
3. `query_api.py` lit `orders_view`.
4. Non. MongoDB est à la fois la seule persistance visible après projection et le Read Model ; le Write Model PostgreSQL n'est pas encore utilisé.
5. Les responsabilités HTTP sont séparées, mais la partie commande ne possède pas encore de modèle de données persistant et de logique métier distincts.

## Exercice 2

6. `orders` porte l'état courant de la commande ; `order_items` porte les lignes de commande. La séparation correspond à un modèle relationnel normalisé côté écriture.
7. `orders_view` est le Read Model. Elle doit pouvoir être reconstruite et organisée pour les requêtes ; elle ne doit pas devenir la source de vérité des commandes.
8. `orders.version` représente la version métier courante de l'agrégat commande.
9. `outbox_events.aggregate_version` indique la version de l'agrégat à laquelle correspond l'événement. Elle permet au Projector de détecter les doublons et les événements plus anciens.

## Exercice 3

10. Parce que la Query Side est indépendante du modèle d'écriture. La Command Side doit modifier PostgreSQL, puis publier un événement ; le Projector construit MongoDB.
11. Pour garantir que l'état métier et l'événement à publier sont persistés ensemble. Si la transaction est annulée, ni la commande ni l'événement ne sont conservés.
12. Toute la transaction PostgreSQL est rollbackée : la commande partiellement créée n'est pas conservée et aucun événement Outbox n'est validé.
13. HTTP 400 dans la solution proposée : le client demandé n'existe pas.

## Exercice 4

14. `INSERT PostgreSQL` réussit, puis Kafka devient indisponible avant la publication. PostgreSQL connaît la commande, mais MongoDB ne peut pas la projeter.
15. PostgreSQL et Kafka ont deux mécanismes de transaction indépendants dans cette implémentation. Il n'y a pas de commit atomique couvrant les deux systèmes.
16. L'Outbox permet de rendre atomique la persistance de l'état métier et de l'intention de publication dans PostgreSQL. Un publisher réessaie ensuite la publication Kafka.

## Exercice 5

17. Pour éviter de perdre définitivement un événement dont la publication aurait échoué.
18. Le même événement peut être publié à nouveau lors d'un prochain passage. On accepte donc une sémantique de type at-least-once et on rend le Projector idempotent.
19. Parce qu'un doublon Kafka ne doit pas modifier plusieurs fois l'état métier de la vue.

## Exercice 6

20. `aggregate_version` représente explicitement l'ordre logique des changements pour une commande. Une date seule ne constitue pas une garantie suffisante d'ordre métier.
21. Il l'ignore.
22. Il l'ignore également afin de ne pas revenir à un état plus ancien.

## Exercice 7

23. L'INSERT PostgreSQL est validé avant la propagation Outbox -> Kafka -> Projector -> MongoDB.
24. On parle de cohérence éventuelle.
25. `PostgreSQL -> outbox_events -> outbox_publisher -> Kafka -> projector -> MongoDB`.

## Exercice 8

26. Parce que MongoDB contient une projection dérivée des événements, et non la source de vérité du Write Model.
27. Pour un nouveau groupe sans offset initial, Kafka demande de commencer au plus ancien offset encore disponible.
28. La politique de rétention Kafka peut avoir supprimé les plus anciens événements. `earliest` signifie le plus ancien offset disponible, pas un historique éternel.

## Exercice 9

| Élément | Command Side / Write Side | Query Side / Read Side |
|---|---|---|
| API | `command_api.py` / Flask :5000 | `query_api.py` / Flask :5001 |
| Base | PostgreSQL | MongoDB |
| Modèle | `orders`, `order_items`, `customers` | `orders_view` |
| Objectif | appliquer les commandes et règles métier | répondre efficacement aux requêtes |
| Kafka | production d'événements via l'Outbox Publisher | consommation d'événements par le Projector |

Explication attendue : PostgreSQL est adapté à la cohérence transactionnelle et à la gestion du modèle métier d'écriture. MongoDB est utilisé ici comme modèle de lecture matérialisé, dénormalisé et reconstruit par projection. Kafka découple la publication des changements de leur consommation par le Read Model.

## Points de vigilance formateur

### L'Outbox ne fournit pas exactement une fois

Le publisher peut publier un événement puis tomber en panne avant la mise à jour de `published_at`. Le même événement pourra alors être publié une deuxième fois. La solution assume une sémantique at-least-once.

### Le Projector doit donc être idempotent

La solution compare `aggregate_version` à `last_event_version` avant d'appliquer l'événement.

### CQRS n'est pas synonyme de Kafka

CQRS est une séparation de responsabilités et de modèles. Kafka est ici le mécanisme de transport événementiel choisi pour relier le Write Side au Read Side.

### CQRS n'implique pas obligatoirement Event Sourcing

PostgreSQL peut conserver l'état courant du Write Model. Le TP ne constitue donc pas un Event Sourcing complet.
