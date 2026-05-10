import couchdb
from connectors.base_connector import BaseConnector

class CouchDBConnector(BaseConnector):

    def __init__(self):
        self.server = None

    def connect(self, url="http://localhost:5984",
                username="admin", password="admin123", **kwargs) -> bool:
        try:
            self.server = couchdb.Server(url)
            self.server.resource.credentials = (username, password)
            list(self.server)
            return True
        except Exception as e:
            print(f"CouchDB connection error: {e}")
            return False

    def get_collections(self, db_name: str = "") -> list:
        """Retourne toutes les bases CouchDB (= équivalent des collections)"""
        try:
            return [db for db in self.server if not db.startswith("_")]
        except Exception as e:
            print(f"Erreur get_collections CouchDB: {e}")
            return []

    def get_documents(self, db_name: str, collection_name: str, limit=None) -> list:
        """collection_name = nom de la base CouchDB"""
        try:
            db = self.server[collection_name]
            docs = []
            for doc_id in db:
                if doc_id.startswith("_design"):
                    continue  # ignorer les design documents
                doc = dict(db[doc_id])
                doc.pop("_id", None)
                doc.pop("_rev", None)
                docs.append(doc)
                if limit and len(docs) >= limit:
                    break
            return docs
        except Exception as e:
            print(f"Erreur get_documents CouchDB: {e}")
            return []

    def close(self):
        self.server = None