# TP — Mettre en œuvre CQRS avec PostgreSQL, Kafka et MongoDB

## Durée indicative

2 h 30 à 3 h 30 selon le niveau du groupe.

## Contexte

Vous disposez d'une application de gestion de commandes construite avec trois composants Python :

- une **Command API** Flask ;
- un **Projector** consommant Kafka ;
- une **Query API** Flask.

Le système actuel produit directement un événement Kafka lors d'une commande puis construit une vue MongoDB. Il manque cependant un véritable **Write Model persistant** côté commande.

Votre objectif est de faire évoluer ce système pour obtenir une implémentation pédagogique de **CQRS événementiel** :

```text
WRITE SIDE
Client -> Command API -> PostgreSQL -> Outbox -> Kafka
                                                |
                                                v
READ SIDE
                                          Projector -> MongoDB -> Query API
```

### Vocabulaire à utiliser

- **Command** : intention de modifier l'état métier.
- **Write Model** : modèle PostgreSQL représentant l'état métier courant.
- **Domain Event** : événement décrivant un changement qui a été accepté.
- **Outbox** : table PostgreSQL contenant les événements à publier.
- **Projector** : composant qui transforme les événements en Read Model.
- **Read Model** : vue MongoDB adaptée aux requêtes.
- **Cohérence éventuelle** : le Read Model peut être temporairement en retard sur le Write Model.

## Architecture cible

```text
                         CLIENT
                           |
              +------------+------------+
              |                         |
              v                         v
       +---------------+         +---------------+
       | Command API   |         | Query API     |
       | Flask :5000   |         | Flask :5001   |
       +-------+-------+         +-------^-------+
               |                         |
               v                         |
       +------------------+              |
       | PostgreSQL       |              |
       | WRITE MODEL      |              |
       | orders           |              |
       | order_items      |              |
       | customers        |              |
       | outbox_events    |              |
       +--------+---------+              |
                |                        |
                v                        |
       +------------------+              |
       | Outbox Publisher |              |
       +--------+---------+              |
                |                        |
                v                        |
             +------+                    |
             |Kafka | orders.events      |
             +--+---+                    |
                |                        |
                v                        |
       +------------------+              |
       | Projector        |              |
       +--------+---------+              |
                |                        |
                v                        |
       +------------------+              |
       | MongoDB          |--------------+
       | READ MODEL       |
       | orders_view      |
       +------------------+
```

---

# Exercice 1 — Observer le système existant

### Travail demandé

1. Lancer le `command_api.py`, `projector.py` et `query_api.py` du dossier `socle_initial`.
2. Créer une commande pour le client `C001`.
3. Observer le topic Kafka `orders.events`.
4. Observer la collection MongoDB `training.orders_view`.
5. Interroger la commande avec la Query API.

### Questions

1. Où la commande est-elle persistée au moment du retour HTTP ?
2. Quel composant écrit dans MongoDB ?
3. Quel composant lit MongoDB ?
4. Le système possède-t-il déjà un Write Model distinct du Read Model ?
5. Pourquoi peut-on déjà parler d'une séparation Command/Query, mais pas encore d'un CQRS pleinement représentatif ?

---

# Exercice 2 — Construire le Write Model PostgreSQL

Le schéma SQL fourni dans `sql/init_postgresql.sql` crée quatre tables :

- `customers`
- `orders`
- `order_items`
- `outbox_events`

### Travail demandé

1. Exécuter le script SQL.
2. Vérifier les données de `customers`.
3. Décrire le rôle de chaque table.
4. Identifier les informations qui relèvent du Write Model et celles qui relèvent du Read Model.

### Questions

1. Pourquoi `orders` et `order_items` sont-ils séparés ?
2. Pourquoi `orders_view` n'est-elle pas utilisée pour les opérations d'écriture ?
3. Quel est le rôle de `version` dans `orders` ?
4. Quel est le rôle de `aggregate_version` dans `outbox_events` ?

---

# Exercice 3 — Transformer la Command API

À partir de `eleve/command_api.py`, implémenter la création d'une commande.

## Contraintes

Pour `POST /orders` :

1. `customer_id` est obligatoire.
2. `items` doit être une liste non vide.
3. chaque article possède `product_id`, `quantity` et `unit_price`.
4. `quantity` doit être strictement positif.
5. `unit_price` doit être positif ou nul.
6. le client doit exister dans PostgreSQL.
7. la commande doit être insérée dans `orders`.
8. les articles doivent être insérés dans `order_items`.
9. un événement `OrderCreated` doit être inséré dans `outbox_events`.
10. les trois types d'écriture doivent faire partie de **la même transaction PostgreSQL**.
11. la Command API ne doit pas publier directement dans Kafka.

### Questions

1. Pourquoi ne doit-on pas écrire directement dans MongoDB depuis `command_api.py` ?
2. Pourquoi l'événement doit-il être enregistré dans PostgreSQL dans la même transaction que la commande ?
3. Que doit-il se passer si l'insertion d'un article échoue ?
4. Quelle réponse HTTP retourner pour un client inexistant ?

---

# Exercice 4 — Comprendre et résoudre le problème du dual write

Imaginez l'implémentation suivante :

```text
INSERT PostgreSQL
COMMIT
   |
   v
producer.send(Kafka)
```

### Questions

1. Décrire un scénario dans lequel PostgreSQL est à jour mais Kafka ne contient pas l'événement.
2. Décrire l'effet sur MongoDB.
3. Pourquoi une simple écriture séquentielle dans deux systèmes ne constitue-t-elle pas une transaction distribuée ?
4. À quoi sert alors la table `outbox_events` ?

---

# Exercice 5 — Implémenter l'Outbox Publisher

Compléter `eleve/outbox_publisher.py`.

Le programme doit :

1. récupérer régulièrement les lignes où `published_at IS NULL` ;
2. publier `payload` dans le topic `orders.events` ;
3. utiliser `aggregate_id` comme clé Kafka ;
4. attendre la confirmation de la publication ;
5. renseigner `published_at` uniquement après confirmation ;
6. continuer à fonctionner en boucle.

### Questions

1. Pourquoi ne marque-t-on pas l'événement comme publié avant l'envoi Kafka ?
2. Que peut-il se passer si le programme tombe en panne après Kafka mais avant `UPDATE outbox_events` ?
3. Quelle propriété doit donc posséder le Projector pour supporter ce cas ?

---

# Exercice 6 — Rendre le Projector idempotent

Le Projector initial applique directement les événements à MongoDB.

Compléter `eleve/projector.py` pour utiliser `aggregate_version`.

### Règle

Un événement ne doit être appliqué que si :

```text
aggregate_version > last_event_version
```

### Tests demandés

1. créer une commande ;
2. observer la projection ;
3. annuler la commande ;
4. vérifier la version 2 dans MongoDB ;
5. republier artificiellement l'événement de création ;
6. vérifier que l'état `CANCELLED` n'est pas réécrit en `CREATED`.

---

# Exercice 7 — Observer la cohérence éventuelle

Lancer simultanément les quatre composants.

Créer ensuite une commande et effectuer immédiatement une requête sur la Query API.

### Questions

1. PostgreSQL peut-il contenir la commande avant MongoDB ?
2. Pourquoi ?
3. Quel composant crée la latence entre les deux ?
4. Ce comportement constitue-t-il un bug ou une propriété de l'architecture ?

---

# Exercice 8 — Reconstruire le Read Model

1. Créer au moins trois commandes.
2. Vérifier leur présence dans PostgreSQL.
3. Vérifier leur présence dans MongoDB.
4. Vider la collection `orders_view`.
5. Relancer le Projector.
6. Vérifier que les données peuvent être reconstruites à partir des événements Kafka encore disponibles.

### Questions

1. Pourquoi le Read Model peut-il être détruit puis reconstruit ?
2. Quel est l'intérêt de cette propriété ?
3. Dans quelles conditions le rejeu ne permettrait-il pas de reconstruire tout l'historique ?

---

# Exercice 9 — Synthèse CQRS

Compléter le tableau :

| Élément | Command Side / Write Side | Query Side / Read Side |
|---|---|---|
| API | ? | ? |
| Base de données | ? | ? |
| Objectif | ? | ? |
| Format des données | ? | ? |
| Flux Kafka | ? | ? |

Puis rédiger en cinq lignes maximum l'explication du choix PostgreSQL + MongoDB.

---

# Livrables élèves

- `command_api.py` complété ;
- `outbox_publisher.py` complété ;
- `projector.py` complété ;
- réponses à `QUESTIONS_TP_CQRS.md` ;
- preuves d'exécution : réponses HTTP et quelques vérifications PostgreSQL/MongoDB/Kafka.
