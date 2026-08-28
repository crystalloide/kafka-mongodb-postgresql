# Installation et démarrage

## 1. Prérequis

Le socle technique du handlab doit fournir :

- Kafka accessible sur `localhost:9092,localhost:9094,localhost:9096` (ou via `KAFKA_BOOTSTRAP`) ;
- MongoDB accessible via `MONGO_URI` ;
- PostgreSQL accessible via `POSTGRES_DSN` ;
- Python 3.11+ recommandé.

## 2. Installer les dépendances

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## 3. Variables d'environnement

Copier `.env.example` vers `.env` puis adapter les valeurs à l'environnement du handlab.

```bash
set -a
source .env
set +a
```

```bash
echo $POSTGRES_DSN
```

## 4. Initialiser PostgreSQL

Depuis `psql` :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_CQRS/
psql "$POSTGRES_DSN" -f sql/init_postgresql.sql
```

Le script crée les tables du Write Model et de l'Outbox et insère deux clients de test.

## 5. Créer le topic Kafka

Si le topic n'existe pas déjà :

```bash
kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --topic orders.events \
  --partitions 3 \
  --replication-factor 3
```

Adapter la commande à l'installation Kafka fournie avec le handlab.

## 6. Lancer les composants

Terminal 1 :

```bash
python solution/outbox_publisher.py
```

Terminal 2 :

```bash
python solution/projector.py
```

Terminal 3 :

```bash
python solution/command_api.py
```

Terminal 4 :

```bash
python solution/query_api.py
```

## 7. Vérification

Créer une commande :

```bash
curl -X POST http://localhost:5000/orders \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C001","items":[{"product_id":"P001","quantity":2,"unit_price":25.0},{"product_id":"P002","quantity":1,"unit_price":50.0}]}'
```

Puis lire :

```bash
curl http://localhost:5001/orders/<ORDER_ID>
```

Annuler :

```bash
curl -X POST http://localhost:5000/orders/<ORDER_ID>/cancel
```

Relire :

```bash
curl http://localhost:5001/orders/<ORDER_ID>
```
