# connectors/base_connector.py
from abc import ABC, abstractmethod

class BaseConnector(ABC):

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Établir la connexion. Retourne True si succès."""
        pass

    @abstractmethod
    def get_collections(self, db_name: str) -> list:
        """Retourne la liste des collections/tables."""
        pass

    @abstractmethod
    def get_documents(self, db_name: str, collection_name: str, limit=None) -> list:
        """Retourne les documents sous forme de liste de dicts Python."""
        pass

    @abstractmethod
    def close(self):
        """Fermer la connexion."""
        pass