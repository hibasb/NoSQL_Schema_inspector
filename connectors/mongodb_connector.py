# connectors/mongodb_connector.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from connectors.base_connector import BaseConnector

class MongoDBConnector(BaseConnector):

    def __init__(self):
        self.client = None

    def connect(self, uri="mongodb://localhost:27017", **kwargs) -> bool:
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
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