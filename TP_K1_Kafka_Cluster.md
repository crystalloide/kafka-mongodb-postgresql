## TP K1 — Cluster KRaft, topics et CLI

**Durée** : 30 min

**Prérequis** :
- Environnement Docker Compose démarré (Kafka 3.8.1 KRaft, Kafka UI, Kafka Connect, PostgreSQL, MongoDB).
- venv Python activé (pour les TP suivants), mais **non utilisé** dans ce TP.
- Fichier `.env` avec `KAFKA_BOOTSTRAP` et `KAFKA_UI` configurés.

## Objectifs

- Découvrir le cluster Kafka en mode **KRaft** (3 nœuds broker/controller) via Kafka UI.
- Créer un topic avec **facteur de réplication = 3** et comprendre l’impact de `min.insync.replicas` et `acks`.
- Créer deux topics applicatifs `orders.commands` et `orders.events` avec 3 partitions chacun.

---

## 0. Découverte du cluster via Kafka UI (10 min)

Ouvrez Kafka UI dans votre navigateur :

- URL (depuis le `.env`) : `KAFKA_UI=http://localhost:8080`.

Dans l’interface Kafka UI :

1. Allez dans l’onglet **Cluster** :
   - Vérifiez le nombre de **brokers** (3).
   - Identifiez le **controller** du cluster (mode KRaft — plus de ZooKeeper).

2. Allez dans l’onglet **Topics** :
   - Listez les topics existants (topics système comme `_connect-configs`, `_connect-offsets`, etc.).
   - Pour un topic, observez :
     - Le nombre de **partitions**.
     - Le **Replication Factor** (nombre de copies de chaque partition).
     - Les **ISR** (In‑Sync Replicas) : répliques à jour avec le leader.

### Questions à poser

- Que signifie le **Replication Factor** d’un topic ?
- Qu’est‑ce qu’un **isr** (In‑Sync Replica) et pourquoi est‑ce important pour la durabilité ?

---

## 1. Création d’un topic en CLI avec RF=3 (10 min)

Objectif : créer un topic `demo.rf3` avec 3 partitions et un facteur de réplication de 3, puis discuter de `min.insync.replicas` et `acks`.

Dans un terminal de l’hôte, exécutez la commande suivante (formateur ou stagiaires avancés) :

```bash
docker exec -it kafka1 \
  /usr/bin/kafka-topics \
  --bootstrap-server kafka1:19092,kafka2:19092,kafka3:19092 \
  --create \
  --topic demo.rf3 \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2
```


### À expliquer

- `--replication-factor 3` : chaque partition existe sur **3 brokers** (1 leader + 2 followers).
- `min.insync.replicas=2` :
  - Pour un producteur configuré avec `acks=all`, l’écriture est considérée comme **réussie** uniquement si **au moins 2 répliques** (leader + 1 follower) confirment la réception.
  - Si moins de 2 ISR sont disponibles, le broker renvoie une erreur (ex. `NotEnoughReplicas`) et le producteur doit gérer ce cas.
- Noter la réserve sur la nomenclature (dans le nom des topics, on peut utiliser '.' ou '_' mais pas les deux) :
```text
WARNING: Due to limitations in metric names, topics with a period ('.') or underscore ('_') could collide. To avoid issues it is best to use either, but not both.
```

### Vérification dans Kafka UI

1. Rafraîchissez l’onglet **Topics**.
2. Sélectionnez le topic `demo.rf3` :
   - Vérifiez **Partition count = 3**.
   - Vérifiez **Replication factor = 3**.
   - Pour chaque partition, notez :
     - Le broker **Leader**.
     - Les brokers **Replicas** et **In‑Sync Replicas (ISR)**.

### Discussion rapide

- Avec `replication.factor=3` et `min.insync.replicas=2`, on peut perdre **un broker** sans interrompre les écritures en `acks=all`.
- Si 2 brokers sur 3 tombent, il ne reste plus assez d’ISR pour satisfaire `min.insync.replicas=2` et les écritures sont refusées (durabilité privilégiée). 

---

## 2. Exercice — Créer les topics `orders.commands` et `orders.events` (10 min)

Objectif : créer les deux topics applicatifs qui seront utilisés dans les TP Kafka suivants et dans la partie CQRS.

### 2.1 Création en CLI

Dans le même terminal :

```bash
# Topic des commandes (côté Command)
docker exec -it kafka1 \
  /usr/bin/kafka-topics \
  --bootstrap-server kafka1:19092,kafka2:19092,kafka3:19092 \
  --create \
  --topic orders.commands \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2

# Topic des événements (côté Event)
docker exec -it kafka1 \
  /usr/bin/kafka-topics \
  --bootstrap-server kafka1:19092,kafka2:19092,kafka3:19092 \
  --create \
  --topic orders.events \
  --partitions 3 \
  --replication-factor 3 \
  --config min.insync.replicas=2
```

### 2.2 Variante via Kafka UI (optionnel)

Regardons la création via Kafka UI :

1. Bouton **+ Add a Topic**. en haut à droite de l'écran
2. Renseignez :
   - `Topic name` : `orders.commands` ou `orders.events`.
   - `Number of Partitions` : `3`.
   - `Cleanup policy` : Delete
   - `Min in Sync Replicas` : `2`.
   - `Replication factor` : `3`.

### 2.3 Vérification

Dans Kafka UI :

- Vérifiez que les topics `orders.commands` et `orders.events` apparaissent bien.
- Inspectez chacun :
  - **3 partitions**.
  - **Replication factor = 3**.
  - ISR complet (3 répliques) tant que tous les brokers sont healthy.

### Questions de réflexion

- Pourquoi choisir **3 partitions** pour ces topics applicatifs ? (Répartition de la charge, parallélisme des consommateurs.)
- Que se passerait‑il si on mettait `min.insync.replicas=1` pour ces topics critiques ? (Plus de disponibilité, mais moins de garantie de durabilité en cas de crash du leader.)

---

## 3. Synthèse pédagogique

- Kafka KRaft permet de piloter le cluster sans ZooKeeper, tout en conservant les concepts de partitions, réplication et ISR.
- Le couple `replication.factor` / `min.insync.replicas`, combiné avec `acks`, détermine le **compromis entre disponibilité et durabilité** des écritures.
- Les topics `orders.commands` et `orders.events` créés dans ce TP serviront de base aux TPs suivants sur le producteur/consommateur Kafka et l’architecture CQRS.
