# connectors/documentdb_connector.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from connectors.base_connector import BaseConnector

class DocumentDBConnector(BaseConnector):

    def __init__(self):
        self.client = None

    def connect(self, uri="", tls=True, tls_ca_file="rds-combined-ca-bundle.pem", **kwargs) -> bool:
        try:
            self.client = MongoClient(
                uri,
                tls=tls,
                tlsCAFile=tls_ca_file,
                serverSelectionTimeoutMS=5000
            )
            self.client.admin.command("ping")
            return True
        except ConnectionFailure:
            return False

    def get_collections(self, db_name: str) -> list:
        try:
            return self.client[db_name].list_collection_names()
        except Exception:
            return []

    def get_documents(self, db_name: str, collection_name: str, limit=None) -> list:
        collection = self.client[db_name][collection_name]
        cursor = collection.find({}, {"_id": 0})
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def close(self):
        if self.client:
            self.client.close()