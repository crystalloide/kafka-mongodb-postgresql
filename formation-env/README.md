# Environnement de formation Python — Kafka / PostgreSQL / MongoDB

## Correctif appliqué (v7)

Deux problèmes lors de la connexion Hawtio -> Jolokia des brokers :

1. **"Host not whitelisted"** : Hawtio n'autorise par défaut que
   `localhost`/`127.0.0.1` pour se connecter à un JMX distant, pour
   des raisons de sécurité. Ajout de
   `-Dhawtio.proxyAllowlist=* -Dhawtio.proxyWhitelist=*` (les deux
   noms de propriété selon la version) via `JAVA_TOOL_OPTIONS` sur le
   conteneur `hawtio`, ce qui autorise la connexion à `kafka1`,
   `kafka2`, `kafka3`.
2. **Chemin Jolokia incorrect** : dans le formulaire "Add Connection",
   le champ *Path* doit être `/jolokia` (et non `/hawtio/jolokia`) :
   l'agent Jolokia embarqué dans les brokers expose son API
   directement à la racine du port 8778.

## Connexion à un broker depuis Hawtio

Dans `http://localhost:8888/hawtio` → **Connect** → **Add connection** :

| Champ | Valeur |
|---|---|
| Name | kafka1 |
| Scheme | http |
| Host | kafka1 |
| Port | 8778 |
| Path | /jolokia |

Cliquez sur **Test Connection** : le message d'erreur "Host not
whitelisted" doit avoir disparu après application du correctif v7.
Répétez pour `kafka2:8779` et `kafka3:8780` si vous testez depuis
l'extérieur du réseau Docker, ou gardez le port 8778 pour les 3 si
vous êtes connecté depuis l'intérieur du réseau `formation-net`.

## Historique des correctifs précédents

- v2/v3 : remplacement des images Hawtio tierces retirées de Docker
  Hub par un build local depuis le jar officiel Maven Central.
- v4/v5 : agent Jolokia corrigé (version 2.2.9, artefact renommé,
  vérification via `jar tf`).
- v6 : port Kafka UI (8080 → 8082 si conflit sur votre machine).
- v7 (ce ZIP) : whitelist Hawtio + chemin Jolokia corrigé.

## Démarrage

```bash
cd formation-env
docker compose build --no-cache hawtio
docker compose up -d
```

Pas besoin de reconstruire les brokers Kafka (déjà fonctionnels),
seul le conteneur `hawtio` change.
