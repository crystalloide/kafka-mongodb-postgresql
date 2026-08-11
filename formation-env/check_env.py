"""
check_env.py
Script de vérification rapide de l'environnement de formation
Kafka (métadonnées cluster) + MongoDB (ping), avec gestion de
l'authentification sur les deux services.

Usage :
    python check_env.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

RESULTS = []  # (nom_check, ok: bool, message: str)


def check_kafka():
    """Se connecte au cluster Kafka (avec authentification SASL si
    configurée) et récupère les métadonnées (brokers, topics)."""
    from kafka import KafkaAdminClient
    from kafka.errors import KafkaError, NoBrokersAvailable

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    servers = bootstrap.split(",")

    # Authentification Kafka (optionnelle) : PLAINTEXT par défaut,
    # bascule vers SASL_PLAINTEXT/SASL_SSL si des identifiants sont fournis.
    security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
    sasl_username = os.getenv("KAFKA_SASL_USERNAME")
    sasl_password = os.getenv("KAFKA_SASL_PASSWORD")

    admin_kwargs = {
        "bootstrap_servers": servers,
        "client_id": "check-env",
        "request_timeout_ms": 5000,
        "security_protocol": security_protocol,
    }

    if sasl_username and sasl_password:
        admin_kwargs.update({
            "sasl_mechanism": sasl_mechanism,
            "sasl_plain_username": sasl_username,
            "sasl_plain_password": sasl_password,
        })

    try:
        admin = KafkaAdminClient(**admin_kwargs)

        topics = admin.list_topics()

        client_meta = admin._client
        client_meta.poll(timeout_ms=3000)
        brokers = client_meta.cluster.brokers()

        nb_brokers = len(brokers)
        nb_topics = len(topics)

        admin.close()

        auth_info = "authentifié (SASL)" if sasl_username else "sans authentification"
        msg = f"{nb_brokers} broker(s) détecté(s), {nb_topics} topic(s) existant(s) [{auth_info}]"
        RESULTS.append(("Kafka (métadonnées cluster)", True, msg))
        return True

    except NoBrokersAvailable:
        RESULTS.append((
            "Kafka (métadonnées cluster)",
            False,
            "Aucun broker joignable : vérifiez KAFKA_BOOTSTRAP et l'état du cluster."
        ))
        return False
    except KafkaError as e:
        # Les erreurs d'authentification SASL (ex: SaslAuthenticationFailedError)
        # sont des sous-classes de KafkaError.
        if "auth" in type(e).__name__.lower():
            RESULTS.append((
                "Kafka (métadonnées cluster)",
                False,
                f"Authentification refusée : vérifiez KAFKA_SASL_USERNAME/PASSWORD ({e})"
            ))
        else:
            RESULTS.append(("Kafka (métadonnées cluster)", False, f"Erreur Kafka : {e}"))
        return False
    except Exception as e:
        RESULTS.append(("Kafka (métadonnées cluster)", False, f"Erreur inattendue : {e}"))
        return False


def check_mongo():
    """Se connecte à MongoDB (URI authentifiée) et exécute ping,
    en distinguant erreur réseau et erreur d'authentification."""
    from pymongo import MongoClient
    from pymongo.errors import OperationFailure, ServerSelectionTimeoutError, PyMongoError

    # URI par défaut avec identifiants, alignée sur l'environnement de formation
    # (utilisateur "formation" créé sur la base admin).
    mongo_uri = os.getenv(
        "MONGO_URI",
        "mongodb://formation:formation@localhost:27017/?authSource=admin",
    )

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # ping seul ne suffit pas toujours à révéler un problème d'authentification
        # selon la configuration du serveur : on force une commande nécessitant
        # des droits (list_database_names) pour valider l'auth de bout en bout.
        response = client.admin.command("ping")
        dbs = client.list_database_names()

        if response.get("ok") == 1.0:
            msg = f"ping OK, authentifié, {len(dbs)} base(s) visible(s) : {', '.join(dbs) if dbs else 'aucune'}"
            RESULTS.append(("MongoDB (ping)", True, msg))
            client.close()
            return True
        else:
            RESULTS.append(("MongoDB (ping)", False, f"Réponse inattendue : {response}"))
            client.close()
            return False

    except ServerSelectionTimeoutError:
        RESULTS.append((
            "MongoDB (ping)",
            False,
            "Connexion impossible : vérifiez host/port dans MONGO_URI et l'état du conteneur."
        ))
        return False
    except OperationFailure as e:
        RESULTS.append((
            "MongoDB (ping)",
            False,
            f"Authentification refusée : vérifiez user/password/authSource dans MONGO_URI ({e})"
        ))
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
    check_kafka()
    check_mongo()

    global_ok = print_summary()

    sys.exit(0 if global_ok else 1)
