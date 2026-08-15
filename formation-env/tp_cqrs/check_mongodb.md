#### Test en direct de la connexion et de la configuration du ReplicaSet MongoDB :

```bash
cd ~/kafka-mongodb-postgresql/formation-env/tp_m4
```

```bash
python - << 'EOF'
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

uri = os.getenv("MONGO_URI")
print("MONGO_URI =", uri)

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
print("ping:", client.admin.command("ping"))
print("dbs:", client.list_database_names())
EOF
```
