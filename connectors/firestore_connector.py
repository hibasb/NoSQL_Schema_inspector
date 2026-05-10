import firebase_admin
from firebase_admin import credentials, firestore
from connectors.base_connector import BaseConnector
import os

class FirestoreConnector(BaseConnector):

    def __init__(self):
        self.db = None
        self.app = None

    def connect(self, credentials_path="", **kwargs) -> bool:
        try:
            if firebase_admin._apps:
                firebase_admin.delete_app(firebase_admin.get_app())

            # Priorité 1 : fichier JSON si fourni manuellement
            # Priorité 2 : variable d'environnement GOOGLE_APPLICATION_CREDENTIALS
            # Priorité 3 : chemin par défaut dans le projet
            if credentials_path and os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
            elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                cred = credentials.ApplicationDefault()
            else:
                # Cherche dans le dossier du projet automatiquement
                default_path = os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")
                if os.path.exists(default_path):
                    cred = credentials.Certificate(default_path)
                else:
                    print("Aucune credentials trouvée.")
                    return False

            self.app = firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            return True

        except Exception as e:
            print(f"Firestore connection error: {e}")
            return False

    def get_collections(self, db_name: str = "") -> list:
        try:
            return [col.id for col in self.db.collections()]
        except Exception as e:
            print(f"Erreur get_collections: {e}")
            return []

    def get_documents(self, db_name: str, collection_name: str, limit=None) -> list:
        try:
            ref = self.db.collection(collection_name)
            docs = ref.limit(limit).stream() if limit else ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Erreur get_documents: {e}")
            return []

    def close(self):
        try:
            if self.app:
                firebase_admin.delete_app(self.app)
                self.app = None
                self.db = None
        except Exception:
            pass