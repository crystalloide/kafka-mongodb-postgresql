## TP K3 — Supervision via Hawtio/JMX et Redpanda Console

**Durée** : 30 min

**Prérequis** :
- TP K1 et K2 réalisés (topics créés, producteurs/consommateurs opérationnels).
- Environnement Docker Compose démarré :
  - Kafka 3.8.1 KRaft (3 brokers).
  - Hawtio (JMX via Jolokia).
  - Kafka UI.
  - Redpanda Console.
- Fichier `.env` avec les endpoints de supervision :

```text
HAWTIO=http://localhost:8888/hawtio
KAFKA_UI=http://localhost:8080
REDPANDA_CONSOLE=http://localhost:8090
```

## Objectifs

- Se connecter à **Hawtio** pour explorer les MBeans JMX d’un broker Kafka (débit, latence de réplication, `UnderReplicatedPartitions`).
- Utiliser la **Redpanda Console** pour visualiser les messages, schémas et consumer groups en complément de Kafka UI.
- Provoquer volontairement un **retard de consommation** (consumer lag) et l’observer dans les deux consoles.

---

## 0. Vue d’ensemble des outils de supervision (5 min)

Avant de commencer :

- **Kafka UI** : vue globale du cluster (topics, partitions, consumer groups, offsets).
- **Hawtio** : console JMX générique connectée à Jolokia sur les brokers Kafka (MBeans, métriques runtime).
- **Redpanda Console** : UI orientée développeurs pour Kafka, avec vue messages, schemas, consumer lag.

Ce TP se concentre sur Hawtio et Redpanda Console, en complément de ce que vous avez déjà vu dans Kafka UI.

---

## 1. Supervision JMX avec Hawtio (10 min)

Objectif : se connecter à Hawtio, parcourir les MBeans d’un broker Kafka et identifier quelques métriques clés (débit, réplication, partitions sous‑répliquées).

### 1.1 Accès à Hawtio

1. Ouvrez Hawtio dans le navigateur :

   - URL : `http://localhost:8888/hawtio`.

2. Interface :
   - Page d’accueil Hawtio.
   - Menu **JMX** / **Connect** pour ajouter une connexion Jolokia.

### 1.2 Connexion au broker Kafka via Jolokia

Le container `kafka1` expose Jolokia sur le port 8778.

1. Dans Hawtio, ajoutez une connexion JMX :
   - Name : `kafka1`.
   - Scheme : `http`.
   - Host : `kafka1`.
   - Port : `8778`.
   - Path : `/jolokia`.

2. Validez la connexion.

Vous devez voir l’arbre des MBeans JMX du broker Kafka `kafka1`.

### 1.3 Exploration des MBeans Kafka

Dans le menu JMX :

1. Naviguez vers les MBeans Kafka typiques, par exemple :
   - `kafka.server` → métriques du broker (request handler, sessions, etc.).
   - `kafka.cluster` ou `kafka.log` → informations sur les partitions, ISR.

2. Focus sur quelques métriques :
   - **Débit de production/consommation** (requêtes par seconde, bytes in/out par seconde).
   - **Latence de réplication** (temps pour que les ISR rattrapent le leader).
   - **`UnderReplicatedPartitions`** : nombre de partitions pour lesquelles toutes les répliques ne sont pas à jour.

### Questions à poser

- Que signifie une valeur non nulle de `UnderReplicatedPartitions` ?
- Pourquoi ces métriques sont‑elles critiques en production (détection de problèmes de réplication, de performance) ?

---

## 2. Redpanda Console — consumer groups et messages (10 min)

Objectif : utiliser Redpanda Console pour inspecter les consumer groups et les messages, et comparer avec Kafka UI.

### 2.1 Accès à Redpanda Console

1. Ouvrez Redpanda Console dans le navigateur :
   - URL : `http://localhost:8090`.

2. Vue d’accueil :
   - Liste des clusters Kafka (configurée pour se connecter à `kafka1:19092`, `kafka2:19092`, `kafka3:19092`).

### 2.2 Topics et messages

1. Onglet **Topics** :
   - Sélectionnez `orders.events`.
   - Observez : nombre de partitions, replication factor, configuration du topic.

2. Onglet **Messages** / **Data** (selon la version de Redpanda Console) :
   - Lisez quelques messages `OrderCreated` envoyés lors du TP K2.
   - Notez les champs JSON (`event_type`, `payload.order_id`, `payload.customer_id`, `payload.total_amount`).

### 2.3 Consumer groups

1. Onglet **Consumer Groups** :
   - Repérez le groupe `orders-events-group` utilisé dans le TP K2.
   - Pour ce groupe, observez :
     - Les partitions assignées.
     - Le **current offset** par partition.
     - Le **lag** par partition (différence entre offset de fin et offset consommé).

### Comparaison avec Kafka UI

- Dans Kafka UI, faites le parallèle :
  - Vue du consumer group, offsets, lag.
- Demandez aux stagiaires quels éléments Redpanda Console met davantage en avant (visualisation du lag, historique des messages, etc.).

---

## 3. Exercice — Provoquer un retard de consommation (consumer lag) (10 min)

Objectif : créer volontairement un consumer lag sur le groupe `orders-events-group` et l’observer dans Kafka UI et Redpanda Console.

### 3.1 Scénario

1. Assurez‑vous qu’aucun consommateur `orders-events-group` ne tourne.
   - Si `consumer_orders.py` ou `rebalance_consumer.py` est en cours d’exécution, arrêtez‑les (Ctrl+C).

2. Lancez le producteur pour générer des messages :

```bash
cd tp_k2
python producer_orders.py
```

   - Cela envoie plusieurs événements `OrderCreated` sur `orders.events`.

3. Sans lancer de consommateur, observez :
   - Dans **Kafka UI** :
     - Topic `orders.events` → onglet **Consumer groups** → `orders-events-group`.
     - Lag élevé (offset consommé < offset de fin).
   - Dans **Redpanda Console** :
     - Onglet **Consumer Groups** → `orders-events-group`.
     - Lag par partition clairement visible.

### 3.2 Réduction du lag en relançant un consommateur

1. Relancez un consommateur :

```bash
cd tp_k2
python consumer_orders.py
```

2. Observez dans les consoles :
   - Le lag diminue au fur et à mesure que les messages sont consommés.
   - Le current offset se rapproche de l’end offset pour chaque partition.

3. (Optionnel) Lancez une seconde instance de `rebalance_consumer.py` pour montrer :
   - Le rebalancing des partitions entre consommateurs.
   - L’impact sur le lag par partition.

### Questions de réflexion

- Pourquoi le consumer lag est‑il un indicateur clé pour la santé d’une application temps réel ?
- Que se passe‑t‑il si le lag continue de croître (consommateur trop lent, souci de performance ou de volume) ?

---

## 4. Synthèse pédagogique

- Hawtio/JMX permet une **analyse fine** des métriques internes du broker Kafka (JMX/MBeans), utile pour la performance et la réplication.
- Kafka UI et Redpanda Console offrent des vues complémentaires :
  - Kafka UI : vue cluster et administration.
  - Redpanda Console : focus sur les messages, schemas et consumer lag.
- La notion de **consumer lag** est centrale pour surveiller les pipelines de données : ce TP prépare les stagiaires à interpréter ces métriques lors des TP Kafka Connect et CQRS.
