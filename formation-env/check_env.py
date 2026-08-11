"""
check_env.py
Script de vérification rapide de l'environnement de formation
Kafka (métadonnées cluster) + MongoDB (ping).

Usage :
    python check_env.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

RESULTS = []  # (nom_check, ok: bool, message: str)


def check_kafka():
    """Se connecte au cluster Kafka et récupère les métadonnées
    (brokers, topics) via kafka-python."""
    from kafka import KafkaAdminClient
    from kafka.errors import KafkaError

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    servers = bootstrap.split(",")

    try:
        admin = KafkaAdminClient(
            bootstrap_servers=servers,
            client_id="check-env",
            request_timeout_ms=5000,
        )
        cluster = admin.describe_cluster() if hasattr(admin, "describe_cluster") else None

        # describe_cluster() n'existe pas dans toutes les versions du client ;
        # on utilise donc le contrôleur bas niveau pour lister les topics,
        # ce qui force une résolution de métadonnées auprès du cluster.
        topics = admin.list_topics()

        # Récupération des métadonnées brokers via le client interne
        client_meta = admin._client
        client_meta.poll(timeout_ms=3000)
        brokers = client_meta.cluster.brokers()

        nb_brokers = len(brokers)
        nb_topics = len(topics)

        admin.close()

        msg = f"{nb_brokers} broker(s) détecté(s), {nb_topics} topic(s) existant(s)"
        RESULTS.append(("Kafka (métadonnées cluster)", True, msg))
        return True

    except KafkaError as e:
        RESULTS.append(("Kafka (métadonnées cluster)", False, f"Erreur Kafka : {e}"))
        return False
    except Exception as e:
        RESULTS.append(("Kafka (métadonnées cluster)", False, f"Erreur inattendue : {e}"))
        return False


def check_mongo():
    """Se connecte à MongoDB et exécute la commande ping."""
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        response = client.admin.command("ping")

        if response.get("ok") == 1.0:
            dbs = client.list_database_names()
            msg = f"ping OK, {len(dbs)} base(s) visible(s) : {', '.join(dbs) if dbs else 'aucune'}"
            RESULTS.append(("MongoDB (ping)", True, msg))
            client.close()
            return True
        else:
            RESULTS.append(("MongoDB (ping)", False, f"Réponse inattendue : {response}"))
            client.close()
            return False

    except PyMongoError as e:
        RESULTS.append(("MongoDB (ping)", False, f"Erreur MongoDB : {e}"))
        return False
    except Exception as e:
        RESULTS.append(("MongoDB (ping)", False, f"Erreur inattendue : {e}"))
        return False


def print_summary():
    print("\n" + "=" * 55)
    print(" RESUME VERIFICATION ENVIRONNEMENT DE FORMATION")
    print("=" * 55)

    all_ok = True
    for name, ok, message in RESULTS:
        status = "OK " if ok else "KO "
        symbol = "[OK]" if ok else "[KO]"
        print(f"{symbol} {name:<32} : {message}")
        if not ok:
            all_ok = False

    print("=" * 55)
    if all_ok:
        print(" Statut global : OK - environnement pret pour les TP")
    else:
        print(" Statut global : KO - corriger les points ci-dessus avant de commencer")
    print("=" * 55 + "\n")

    return all_ok


if __name__ == "__main__":
    kafka_ok = check_kafka()
    mongo_ok = check_mongo()

    global_ok = print_summary()

    sys.exit(0 if global_ok else 1)
