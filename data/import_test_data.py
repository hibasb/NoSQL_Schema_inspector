"""
import_test_data.py
-------------------
Script d'import des données de test JSON dans MongoDB, CouchDB ou Firestore.
Usage :
    python data/import_test_data.py --db mongodb
    python data/import_test_data.py --db couchdb
    python data/import_test_data.py --db firestore
"""
import json
import argparse
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


# ── MONGODB ───────────────────────────────────────────────────

def import_mongodb(uri="mongodb+srv://viggo_admin:d0pfAaplQOsKasy9@viggocluster.aspjywp.mongodb.net/?appName=viggoCluster", db_name="test_nosql"):
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    collections = {
        "users":        "users_vulnerable.json",
        "transactions": "transactions_vulnerable.json",
        "products":     "products_clean.json",
    }

    for coll_name, filename in collections.items():
        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as f:
            docs = json.load(f)

        db[coll_name].drop()
        db[coll_name].insert_many(docs)
        print(f"  [OK] MongoDB [{db_name}.{coll_name}] - {len(docs)} documents inseres")

    client.close()


# ── COUCHDB ───────────────────────────────────────────────────

def import_couchdb(url="http://localhost:5984", username="admin", password="admin123"):
    import urllib.request
    import base64

    db_name = "test_nosql"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    # Créer la base si elle n'existe pas
    req = urllib.request.Request(f"{url}/{db_name}", method="PUT", headers=headers)
    try:
        urllib.request.urlopen(req)
        print(f"  [OK] CouchDB base '{db_name}' creee")
    except Exception:
        print(f"  [INFO] CouchDB base '{db_name}' existante (OK)")

    # Importer via _bulk_docs
    path = os.path.join(DATA_DIR, "couchdb_bulk.json")
    with open(path, encoding="utf-8") as f:
        bulk = json.load(f)

    data = json.dumps(bulk).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/{db_name}/_bulk_docs",
        data=data, method="POST", headers=headers
    )
    resp = urllib.request.urlopen(req)
    results = json.loads(resp.read())
    ok = sum(1 for r in results if "id" in r and "error" not in r)
    print(f"  [OK] CouchDB [{db_name}] - {ok}/{len(results)} documents inseres")



# ── FIRESTORE ─────────────────────────────────────────────────

def import_firestore(credentials_path=None):
    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    from google.cloud import firestore
    db = firestore.Client()

    collections = {
        "users":        "users_vulnerable.json",
        "transactions": "transactions_vulnerable.json",
        "products":     "products_clean.json",
    }

    for coll_name, filename in collections.items():
        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as f:
            docs = json.load(f)

        batch = db.batch()
        for i, doc in enumerate(docs):
            ref = db.collection(coll_name).document(f"doc_{i:03d}")
            batch.set(ref, doc)
        batch.commit()
        print(f"  [OK] Firestore [{coll_name}] - {len(docs)} documents inseres")


# ── MAIN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import test data into NoSQL DB")
    parser.add_argument("--db", choices=["mongodb", "couchdb", "firestore"], required=True)
    parser.add_argument("--uri",      default="mongodb://localhost:27017", help="MongoDB URI")
    parser.add_argument("--dbname",   default="nosql_test",               help="MongoDB DB name")
    parser.add_argument("--url",      default="http://localhost:5984",    help="CouchDB URL")
    parser.add_argument("--user",     default="admin",                    help="CouchDB username")
    parser.add_argument("--password", default="admin123",                    help="CouchDB password")
    parser.add_argument("--creds",    default=None,                       help="Firestore service account JSON path")
    args = parser.parse_args()

    print(f"\n[START] Import vers {args.db.upper()}...")

    if args.db == "mongodb":
        import_mongodb(uri=args.uri, db_name=args.dbname)
    elif args.db == "couchdb":
        import_couchdb(url=args.url, username=args.user, password=args.password)
    elif args.db == "firestore":
        import_firestore(credentials_path=args.creds)

    print("\n[DONE] Import termine. Lancez l'app : streamlit run app.py\n")
