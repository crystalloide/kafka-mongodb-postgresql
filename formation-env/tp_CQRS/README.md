# TP CQRS — PostgreSQL + Kafka + MongoDB

Ce TP part d'un exemple existant composé de trois scripts Python :

- `command_api.py` : API d'écriture Flask qui produit actuellement des événements Kafka ;
- `projector.py` : consommateur Kafka qui construit `orders_view` dans MongoDB ;
- `query_api.py` : API de lecture Flask qui interroge `orders_view`.

L'objectif est de faire évoluer cet exemple vers une architecture CQRS plus représentative :

```text
                 WRITE SIDE                                  READ SIDE

Client -> Command API -> PostgreSQL -> Outbox -> Kafka -> Projector -> MongoDB -> Query API
                 |             Write Model                         Read Model       |
                 +-------------------- Commandes -------------------+---------------+
```

Le TP n'implémente pas un Event Sourcing complet. PostgreSQL conserve l'état courant du modèle d'écriture ; Kafka transporte les événements ; MongoDB contient une projection optimisée pour la lecture.

## Contenu

- `ENONCE_TP_CQRS.md` : énoncé élève complet
- `QUESTIONS_TP_CQRS.md` : questions à remettre aux élèves
- `CORRECTION_TP_CQRS.md` : corrigé formateur
- `INSTALLATION.md` : prérequis et lancement
- `sql/init_postgresql.sql` : schéma et données initiales
- `eleve/` : fichiers de départ avec TODO
- `socle_initial/` : version de départ correspondant au TP existant
- `solution/` : solution complète
- `requirements.txt` : dépendances Python
- `.env.example` : variables d'environnement

## Dépendances

Le TP utilise `Flask`, `python-dotenv`, `kafka-python`, `pymongo` et `psycopg`.
