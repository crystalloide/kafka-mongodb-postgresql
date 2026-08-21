
#####  Installation client mongsh sur poste WSL2 Ubntu 24.04

1°) Lancer Ubuntu sur la machine windows (Ubuntu 24.4.1 dans cet exemple) 
```bash
cd ~
cd kafka-mongodb-postgresql/
lsb_release -cs
```
On obtient soit `jammy` (Ubuntu 22.04) soit `noble` (Ubuntu 24.04) => nom de code qu'il faudra utiliser dans le dépôt APT 

2°) Pour s'assurer que les outils nécessaires à l'import de la clé GPG sont présents :
```bash
sudo apt update
sudo apt install -y gnupg curl
```

3°) Installation clé :
```bash
#  Méthode moderne recommandée (l'ancienne `apt-key` est dépréciée).
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
```

Remplacer `jammy` par `noble` pour Ubuntu 24.04 : (notre cas ici) :

```bash
# echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
```


```bash
cd ~
cd kafka-mongodb-postgresql/
sudo apt update
# Ceci installe uniquement le shell (pas le serveur mongod complet), ce qui suffit pour se connecter à une instance distante ou à un conteneur Docker.
sudo apt install -y mongodb-mongosh

```

Voici la méthode officielle via le dépôt APT MongoDB : la plus fiable sur WSL2 puisqu'elle passe par les paquets Debian standards.

Deux points à noter :
- Le paquet mongodb-mongosh installe seulement le shell, pas le serveur mongod. C'est suffisant si MongoDB tourne ailleurs (conteneur Docker, serveur distant, Atlas).
- Alternative plus rapide si tu as déjà Node.js sur ta distro WSL2 : npm install -g mongosh fait le job en une commande, sans dépôt APT à configurer.
 
Pour se connecter au conteneur MongoDB de notre stack kafka-mongodb-postgresql, pensr à l'authSource=admin avec l'utilisateur formation :
```bash
mongosh "mongodb://formation:formation@localhost:27017/?authSource=admin"
```

