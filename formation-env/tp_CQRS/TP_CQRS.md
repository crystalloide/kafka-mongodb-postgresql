# Mini‑application avec le pattern CQRS - Command/Query/Responsibility/Segregation

## Présentation de CQRS

CQRS est un pattern d’architecture qui sépare strictement les opérations d’écriture (commandes) des opérations de lecture (requêtes), chacune avec son propre modèle de données et parfois sa propre base.

## 1. Synthèse de l’approche CQRS

### Définition
**CQRS** (**Command Query Responsibility Segregation**) consiste à utiliser :
- un 1er modèle pour servir les commandes qui modifient l’état (create/update/delete)
- un 2nd modèle distinct pour servir les requêtes qui lisent l’état sans le modifier.

### Principe clé
Au lieu d’avoir un seul modèle/une seule base qui doit à la fois gérer la logique métier complexe et les requêtes de lecture, CQRS autorise :
- un modèle d’écriture optimisé pour la cohérence, les règles métier, les transactions ;
- un modèle de lecture optimisé pour la performance, la dénormalisation, les vues adaptées aux cas d’usage.
  
**Conséquence importante** : Les données lues et les données écrites ne sont plus forcément dans la même structure ni dans la même base, et la lecture devient souvent éventuellement cohérente (il y a un délai entre l’écriture et la mise à jour des vues de lecture).

---

## 2. Schéma de principe pour le TP CQRS (Kafka / PostgreSQL / MongoDB)

**Vue logique de l'architecture :**

**Python** => **API Command** => **kafka `orders.events`** => **kafka connect sink** => **PostgreSQL : table `orders`** (matérialise les écritures - **"Command side"**)
___
**Python** => **API Query** => **kafka `orders.events`** => **kafka consumer (Projector)** => **MongoDB** : **collection `orders_view`** (sert les lectures - **"Query Side"**)

### L’ensemble est typiquement CQRS :
- un modèle et une base pour l’écriture (PostgreSQL via Kafka Connect qui agit comme un Event Store),
- un modèle et une base pour la lecture (MongoDB dénormalisé),
- et Kafka comme bus d’événements au centre.

---

## 0. Préparation de l'environnement

Ouvrez un terminal et activez votre environnement virtuel :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/
python -m venv .venv && source .venv/bin/activate
cd tp_cqrs
```