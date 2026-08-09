#####  Un plugin prévu pour Claude Code est fourni ici : https://github.com/rustyrazorblade/skills

#### L'idée est de porter ce plugin pour un usage moins coûteux avec Google Gemini : 

#### Comme Gemini CLI a été conçu pour être compatible avec l'écosystème de Claude, la transition est très simple.

#### Voici la marche à suivre pas à pas pour transformer ce dépôt "Claude" en un centre de commandes pour Gemini.

#####  Installation

1°) Lancer Ubuntu sur la machine windows (Ubuntu 24.4.1 dans cet exemple) 
```bash
ubuntu
```

2°) Prendre le user souhaité :
```bash
su - user
```

3°) Regarder où nous sommes :
```bash
pwd
```

#####  Étape Pré-requis n°1 : Installation de nodeJS :

```bash
sudo apt remove --purge nodejs npm -y
sudo apt autoremove -y
```

##### Voir ici pour les instructions d'installation de NodeJS :

```bash
https://nodesource.com/products/distributions
```

```bash
sudo apt-get install -y curl
curl -fsSL https://deb.nodesource.com/setup_26.x | sudo -E bash -
sudo apt-get install -y nodejs
```

```bash
node -v   # doit afficher v26.x.x
```

```bash
npm -v    # doit afficher 11.x.x
```


#####  Étape Pré-requis n°2 : Installation ou Mise à jour de npm : 

```bash
sudo npm install -g npm@12.0.2
```

```bash
npm -v    # doit afficher 12.0.2
```
##### Si cela ne suffit pas (version 11 toujours utilisée par défaut) :  

```bash
cd ~
sudo rm -Rf .package
curl -L https://registry.npmjs.org/npm/-/npm-12.0.2.tgz -o npm12.tgz
tar -xzf npm12.tgz
sudo rm -rf /usr/local/lib/node_modules/npm
sudo mv package /usr/local/lib/node_modules/npm
echo '#!/usr/bin/env node require("/usr/local/lib/node_modules/npm/bin/npm-cli.js")' | sudo tee /usr/local/bin/npm > /dev/null
sudo chmod +x /usr/local/bin/npm
```
  
```bash
which npm
npm -v
```

Tu devrais voir :
```text
/usr/local/bin/npm
12.0.2
```


#####  Étape 1 : Installer Gemini CLI

#####  Si vous ne l'avez pas encore, installez l'outil officiel de Google. Il nécessite Node.js (version 18+).

```bash
sudo apt update
sudo apt install -y curl

# Node.js minimum 20+ obligatoire : déjà fait

# Autoriser les scripts natifs (facultatif mais recommandé)
npm config set allow-scripts=@github/keytar,node-pty --location=user

# Installation du CLI
npm install -g @google/gemini-cli@latest

# Vérification
gemini --version

```

#####  Obention d'une clé API  

```bash
echo $GEMINI_API_KEY
```

1. Pour obtenir une clé valide ou "API key" :

Pré-requis : dans Google AI Studio

Go to Google AI Studio.

```bash
https://aistudio.google.com/
```

Se connecter avec son compte Google : 

Générer ou récupérer une clé "API key" et la copier


2. Mettre à jour une variable d'environnement :

Set the valid API key in your current terminal session:

##### Sur linux : 

```bash
export GEMINI_API_KEY="your_actual_api_key_here"
```

##### Sur Windows (invite de commande DOS) :
```bash
set GEMINI_API_KEY=your_actual_api_key_here
```

##### Sur Windows (PowerShell):
```bash
$env:GEMINI_API_KEY="your_actual_api_key_here"
```

#####  Étape 2 : Connexion (Authentification gratuite)

#####  Lancez la commande suivante pour lier votre compte Google. Une fenêtre de navigateur s'ouvrira.

```bash
gemini auth set-key your_actual_api_key_here
```

#####  Note : Cela utilise le tier gratuit (1 000 requêtes/jour).

#####  Étape 3 : Cloner le dépôt de Skills

#####  Nous allons nous appuyer sur le projet et les compétences  de Jon Haddad (rustyrazorblade), qui est un expert renommé de Cassandra.
```bash
cd ~
sudo rm -Rf ~/claude-skills
git clone https://github.com/crystalloide/CassandraIA.git ~/claude-skills
```

#####  Étape 4 : Lier les Skills à Gemini

#####  Gemini cherche ses compétences dans ~/.gemini/skills. 
#####  Nous allons créer un lien symbolique pour que Gemini "voit" les dossiers du dépôt que vous venez de cloner.

#####  Créer le dossier parent pour Gemini
```bash
mkdir -p ~/.gemini/skills
```

#####  Créer un lien symbolique du skill Cassandra vers le dossier Gemini
```bash
sudo rm ~/.gemini/skills/cassandra-expert
ln -s ~/claude-skills/cassandra-expert ~/.gemini/skills/cassandra-expert
```

```bash
ls ~/claude-skills/plugins/cassandra-expert
```

     Gemini va lire le fichier qu'on lui fournira et utiliser les instructions de ~/claude-skills/cassandra-expert/SKILL.md
	 
#####  Étape 5 : Activer les Skills dans Gemini
```bash
gemini skills link ~/claude-skills/plugins/cassandra-expert/skills/expert
```
     
##### Si demandé, saisir le mot de passe 
     
	 Répondre "Y"
	
#####  Étape 6 : On vérifie que le nouveau skills est visible dans Gemini		
```bash	
gemini skills list	
```	
    Loaded cached credentials.
    Discovered Agent Skills:
    
    expert [Enabled]
      Description: General Apache Cassandra expertise for questions, CQL analysis, best practices, vnodes, and guidance. Use for general Cassandra questions that don't fit diagnose, optimize, or data-model.
      Location:    /home/user/.gemini/skills/expert/SKILL.md
    

#####  Cas pratique : Analyse de votre fichier exemple : cassandra.yaml

     Maintenant que le skill "Cassandra Expert" est installé, 
     nous allons l'utiliser sur le fichier que vous avez fourni. 

     Placez-vous dans le dossier où se trouve votre fichier cassandra.yaml

     Lancez la commande suivante :

```bash
cd /endroit du fichier à analyser
##### sous WSL2 : /mnt/c/Users/cryst
cd /mnt/f/
cd '1. Support aux entreprises'
cd '2026 - ... Cassandra'
cd '1. Audit'
cd '0. Informations collectées noeuds Cassandra'
cd 'Production'
```


```bash
 > Analyse mon fichier cassandra.yaml. Est-ce que la configuration des tokens et du stockage est optimale pour un
   cluster de production ?
```

Au bout de quelques minutes, le modèle a identifié le skill à utiliser :

```bash

  Analyse de la configuration Cassandra (cassandra.yaml):
  Analyser la configuration de cassandra.yaml concernant les tokens et le stockage pour un environnement de
  production.

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓  Activate Skill "optimize": Performance optimization for Apache Cassandra clusters. Use when tuning configura… │
│                                                                                                                  │
│ Skill optimize activated. Resources loaded from /home/user/.gemini/skills/optimize:                              │
│                                                                                                                  │
│ Showing up to 200 items (files + folders).                                                                       │
│                                                                                                                  │
│ /home/user/.gemini/skills/optimize/                                                                              │
│ └───SKILL.md                                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ✓  SearchText  'num_tokens' in *cassandra.yaml across all workspace directories → Found 4 matches
  ✓  SearchText  'num_tokens' in *cassandra_latest.yaml across all workspace directories → Found 4 matches

```

##### Pour forcer l'utilisation d'un skill précis :

Pour vous assurer que Gemini applique un skill particulier plutôt qu'un autre :

Nommez directement le skill dans votre consigne.  
```bash
gemini "En utilisant le skill expert, Analyse mon fichier cassandra.yaml. Est-ce que la configuration des tokens et du stockage est optimale pour un
   cluster de production ?"
```


2- Via la commande interactive (en cours de session) :

Saisissez le slash-command suivi du nom de la compétence ou du mot-clé :

```bash
/skill optimize Analyse cette configuration de cluster
```

##### Pour avoir des infos sur Google Gemini CLI :

```bash
/model
```

```bash
/stats
```


##### Affichage complet de la session :

```bash

 ▝▜▄     Gemini CLI v0.54.4
   ▝▜▄
  ▗▟▀    Authenticated with gemini-api-key /auth
 ▝▀


ℹ Positional arguments now default to interactive mode. To run in non-interactive mode, use the --prompt (-p) flag.

ℹ Skipping project agents due to untrusted folder. To enable, ensure that the project root is trusted.

 > Analyse mon fichier cassandra.yaml. Est-ce que la configuration des tokens et du stockage est optimale pour un
   cluster de production ?


 ╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
 │                                                                                                                    │
 │ Do you trust the files in this folder?                                                                             │
 │                                                                                                                    │
 │ Trusting a folder allows Gemini CLI to load its local configurations, including custom commands, hooks, MCP        │
 │ servers, agent skills, and settings. These configurations could execute code on your behalf or change the behavior │
 │ of the CLI.                                                                                                        │
 │                                                                                                                    │
 │                                                                                                                    │
 │ ● 1. Trust folder (extract_etc_cassandra_var_log_vmproa-vincss01)                                                  │
 │   2. Trust parent folder (03. Information cluster nouveau modèle 20 jours données)                                 │
 │   3. Don't trust                                                                                                   │
 │                                                                                                                    │
 ╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


 Gemini CLI is restarting to apply the trust changes...

 ▝▜▄     Gemini CLI v0.54.4
   ▝▜▄
  ▗▟▀    Authenticated with gemini-api-key /auth
 ▝▀


ℹ Positional arguments now default to interactive mode. To run in non-interactive mode, use the --prompt (-p) flag.

 > Analyse mon fichier cassandra.yaml. Est-ce que la configuration des tokens et du stockage est optimale pour un
   cluster de production ?


  Analyse de la configuration Cassandra (cassandra.yaml):
  Analyser la configuration de cassandra.yaml concernant les tokens et le stockage pour un environnement de
  production.

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓  Activate Skill "optimize": Performance optimization for Apache Cassandra clusters. Use when tuning configura… │
│                                                                                                                  │
│ Skill optimize activated. Resources loaded from /home/user/.gemini/skills/optimize:                              │
│                                                                                                                  │
│ Showing up to 200 items (files + folders).                                                                       │
│                                                                                                                  │
│ /home/user/.gemini/skills/optimize/                                                                              │
│ └───SKILL.md                                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ✓  SearchText  'num_tokens' in *cassandra.yaml across all workspace directories → Found 4 matches
  ✓  SearchText  'num_tokens' in *cassandra_latest.yaml across all workspace directories → Found 4 matches
  ✓  SearchText  '_directory|directories' in *cassandra.yaml across all workspace directories → Found 25 matches
  ✓  SearchText  '^[a-z_]+:' in *cassandra.yaml across all workspace directories → Found 100 matches (limited)
  ✓  SearchText  'version|Starting Cassandra' in *system.log across all workspace directories → Found 33 matches

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                      │
│ Usage limit reached for gemini-3.5-flash.                                                                            │
│ /stats model for usage details                                                                                       │
│ /model to switch models.                                                                                             │
│                                                                                                                      │
│                                                                                                                      │
│ ● 1. Keep trying                                                                                                     │
│   2. Stop                                                                                                            │
│                                                                                                                      │
│                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```


###### Autres exemples : 

```bash
gemini "Analyse mon fichier tablestats.txt. Est-ce que certains métriques posent problèmes (nombre de SSTables, Tombstones, etc) pour un cluster de production ?"
```

```bash
gemini "Analyse mon fichier cassandra.yaml. Est-ce que la configuration des tokens et du stockage est optimale pour un cluster de production ?"
```

```bash
gemini "Analyse mon fichier resultat_vmproa-vincss01.txt. Quels sont les paramètres que tu identifies comme étant à améliorer ou corriger pour avoir un fonctionnement optimal pour un cluster de production ?"
``` 

```bash
gemini "Analyse les fichiers de log du noeud cassandra01 vincss01t : vincss01_debug.log, vincss01_gc.log, vincss01_system.log . Quelles sont les anomalies à corriger et les paramètres que tu identifies comme étant à améliorer ou corriger pour avoir un fonctionnement optimal pour un cluster de production ?"
``` 

#####  Ce qui va se passer :

     - Détection : Gemini va scanner ses "Skills" et voir que cassandra-expert correspond au sujet.

     - Activation : Il va charger les instructions du fichier SKILL.md (qui contient des conseils sur les num_tokens, la stratégie de compactage, etc.).

     - Analyse : Il lira votre fichier (notamment votre num_tokens: 16) et vous donnera un avis d'expert.

##### Résultat attendu (Exemple) :

#####   Gemini devrait vous répondre quelque chose comme :

     "En tant qu'expert Cassandra, je vois que vous utilisez num_tokens: 16. 
     C'est une excellente valeur pour les versions récentes (3.0+), 
     car cela réduit l'overhead par rapport aux anciens 256 tokens. 
     Cependant, je remarque que..."

#####  Une astuce de pro 💡 :

     Le dépôt que vous avez cloné contient aussi des "slash commands". 

     Vous pouvez essayer de taper directement ceci dans le terminal Gemini :

```bash
/cql Génère moi une table pour stocker des logs de température
```

     Puisque le skill définit la commande /cql, 
     Gemini l'interprétera immédiatement avec les bonnes pratiques d'expert.


##### Exemple de résultat fourni par l'expert Cassandra IA : 

```text
✦ L'analyse de votre fichier cassandra.yaml montre des points positifs, mais aussi plusieurs points critiques qui pourraient compromettre la stabilité et la
  sécurité d'un cluster en production.

  Voici mon évaluation détaillée :


  1. Configuration des Tokens (Vnodes) - Optimale
   * num_tokens: 16 : C'est un excellent choix pour les versions récentes de Cassandra (3.x/4.x). Cela permet un bon équilibrage de la charge sans surcharger
     le CPU lors des réparations (repairs) ou des compactions.
   * allocate_tokens_for_local_replication_factor: 3 : C'est un paramètre crucial souvent oublié. Il optimise la répartition des tokens en fonction de votre
     facteur de réplication (RF=3), ce qui garantit une distribution de données plus uniforme dès le départ.


  2. Configuration du Stockage - Améliorable
   * Politiques de panne (disk_failure_policy: stop) : C'est correct, mais en production, die est souvent préféré si vous utilisez un orchestrateur (comme
     Kubernetes) ou un gestionnaire de services, afin que le processus soit redémarré proprement au lieu de rester "zombie".
   * Chemins par défaut : Les répertoires (data_file_directories, commitlog_directory) sont commentés, utilisant donc les chemins par défaut. Pour la
     production :
       * Assurez-vous que le CommitLog et les Data Files sont sur des disques physiques séparés (ou au moins des partitions distinctes avec des SSD
         performants) pour éviter les contentions d'I/O.
       * Utilisez impérativement des disques SSD ou NVMe.
   * Débit de compaction (compaction_throughput_mb_per_sec: 64) : Cette valeur est un peu basse pour des disques modernes. Sur des SSD/NVMe, on monte souvent
     à 128, 256, voire on désactive la limite (0) si les ressources le permettent.

  3. Points Critiques et Risques (Production)

  ⚠️ Timeouts excessifs (Danger)
  C'est le point le plus problématique de votre fichier :


   1 read_request_timeout_in_ms: 3600000  # 1 heure !
   2 range_request_timeout_in_ms: 3600000
   3 write_request_timeout_in_ms: 3600000
   4 request_timeout_in_ms: 3600000
  Pourquoi est-ce dangereux ? En production, si un nœud ralentit ou ne répond pas, le coordinateur attendra 1 heure avant d'abandonner. Cela va saturer les
  threads de lecture/écriture (concurrent_reads/writes) et peut faire tomber tout le cluster par effet domino.
   * Recommandation : Revenez à des valeurs raisonnables (ex: 5000 à 10000 ms pour les lectures/écritures, et peut-être plus pour les range_request si
     nécessaire, mais jamais 1 heure).


  ⚠️ Sécurité inexistante
   1 authenticator: AllowAllAuthenticator
   2 authorizer: AllowAllAuthorizer
  N'importe qui ayant accès au réseau peut lire, modifier ou supprimer toutes vos données.
   * Recommandation : Changez pour PasswordAuthenticator et CassandraAuthorizer.


  4. Performance et Réglages Fins
   * concurrent_compactors: 8 : Vous l'avez augmenté, ce qui est bien si vous avez beaucoup de cœurs et des SSD.
   * memtable_allocation_type: heap_buffers : Pour des heaps importants (> 8 Go), envisagez offheap_objects pour réduire la pression sur le Garbage Collector
     (GC).
   * concurrent_reads / writes : Ils sont à 32. Sur des serveurs avec beaucoup de cœurs et des disques NVMe, vous pourriez augmenter ces valeurs (ex: 64 ou
     128) après tests de charge.


  Résumé de mon avis :
  Votre configuration des tokens est très bonne. Cependant, la configuration globale n'est pas prête pour la production à cause des timeouts extrêmes et de
  l'absence de sécurité.

```
