# Questions à remettre — TP CQRS

## Exercice 1

1. Où la commande est-elle persistée au moment du retour HTTP dans le système initial ?
2. Quel composant écrit dans MongoDB ?
3. Quel composant lit MongoDB ?
4. Le système initial possède-t-il déjà un Write Model distinct ?
5. Pourquoi peut-on parler de séparation Command/Query sans encore avoir un CQRS complet ?

## Exercice 2

6. Pourquoi `orders` et `order_items` sont-ils séparés ?
7. Pourquoi `orders_view` n'est-elle pas utilisée pour les écritures ?
8. Quel est le rôle de `orders.version` ?
9. Quel est le rôle de `outbox_events.aggregate_version` ?

## Exercice 3

10. Pourquoi la Command API ne doit-elle pas écrire directement dans MongoDB ?
11. Pourquoi `orders`, `order_items` et `outbox_events` doivent-ils être écrits dans la même transaction ?
12. Que se passe-t-il si l'insertion d'un article échoue ?
13. Quelle réponse HTTP retourner pour un client inexistant ?

## Exercice 4

14. Décrire un scénario de dual write incohérent.
15. Pourquoi une écriture PostgreSQL puis une écriture Kafka ne constitue-t-elle pas une transaction distribuée ?
16. Quel problème l'Outbox résout-il ?

## Exercice 5

17. Pourquoi ne marque-t-on `published_at` qu'après confirmation Kafka ?
18. Que se passe-t-il en cas de crash entre publication Kafka et marquage PostgreSQL ?
19. Pourquoi le Projector doit-il être idempotent ?

## Exercice 6

20. Pourquoi `aggregate_version` est-il préférable à une simple comparaison de dates pour ce TP ?
21. Que doit faire le Projector face à un événement déjà traité ?
22. Que doit-il faire face à un événement plus ancien que celui déjà projeté ?

## Exercice 7

23. Pourquoi PostgreSQL peut-il être à jour avant MongoDB ?
24. Comment nomme-t-on cette caractéristique ?
25. Quelle est la chaîne de propagation entre les deux bases ?

## Exercice 8

26. Pourquoi le Read Model est-il reconstruisible ?
27. Quel rôle joue `auto_offset_reset="earliest"` pour un nouveau groupe consommateur ?
28. Pourquoi ne peut-on pas garantir que tous les événements historiques sont encore disponibles dans Kafka ?

## Exercice 9

29. Compléter le tableau Command Side / Query Side.
30. Expliquer en cinq lignes pourquoi PostgreSQL et MongoDB ont des rôles différents dans cette architecture.
