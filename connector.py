from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, InvalidName

def get_connection(uri="mongodb://localhost:27017"):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        print("Connexion MongoDB réussie !")
        return client
    except ConnectionFailure:
        print("Impossible de se connecter à MongoDB. Vérifiez que le serveur est lancé.")
        return None

def get_collection(client, db_name, collection_name):
    try:
        db = client[db_name]
        collection = db[collection_name]
        count = collection.count_documents({})
        print(f"Collection '{collection_name}' chargée => {count} documents trouvés")
        return collection
    except InvalidName as e:
        print(f"Nom invalide : {e}")
        return None

def get_documents(collection, limit=None):
    if limit:
        documents = list(collection.find({}, {"_id": 0}).limit(limit))
    else:
        documents = list(collection.find({}, {"_id": 0}))
    print(f"{len(documents)} documents récupérés")
    return documents

def get_collections_list(client, db_name):
    try:
        db = client[db_name]
        return db.list_collection_names()
    except Exception as e:
        print(f"Erreur lors de la récupération des collections : {e}")
        return []