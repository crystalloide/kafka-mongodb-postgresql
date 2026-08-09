# Environnement de formation Python — Kafka / PostgreSQL / MongoDB

## Correctif appliqué (v8)

`redpanda-console` refusait de démarrer :
`'config.Config' has invalid keys: connect` (validation YAML stricte).
La clé de configuration racine pour Kafka Connect s'appelle désormais
**`kafkaConnect`** (et non `connect`) dans les versions récentes de
Redpanda Console. Corrigé dans `docker-compose.yml`.

## Correctif appliqué (v7)

Deux problèmes lors de la connexion Hawtio -> Jolokia des brokers :

1. **"Host not whitelisted"** : ajout de
   `-Dhawtio.proxyAllowlist=* -Dhawtio.proxyWhitelist=*` via
   `JAVA_TOOL_OPTIONS` sur le conteneur `hawtio`.
2. **Chemin Jolokia** : dans "Add Connection", le champ *Path* doit
   être `/jolokia` (pas `/hawtio/jolokia`).

## Connexion à un broker depuis Hawtio

`http://localhost:8888/hawtio` → **Connect** → **Add connection** :

| Champ | Valeur |
|---|---|
| Name | kafka1 |
| Scheme | http |
| Host | kafka1 |
| Port | 8778 |
| Path | /jolokia |

## Historique des correctifs précédents

- v2/v3 : images Hawtio tierces retirées de Docker Hub → build local
  depuis le jar officiel Maven Central.
- v4/v5 : agent Jolokia corrigé (version 2.2.9, vérification `jar tf`).
- v6 : port Kafka UI (8080 → 8082 si conflit).
- v7 : whitelist Hawtio + chemin Jolokia.
- v8 (ce ZIP) : clé `kafkaConnect` pour Redpanda Console.

## Démarrage

```bash
cd formation-env
docker compose up -d
docker compose ps
```
