from connector import get_connection, get_collection, get_documents

#Connexion
client = get_connection()

#Charger la collection
collection = get_collection(client, "nosql_inspector_db", "employees")

#Récupérer les documents
documents = get_documents(collection)

#Afficher
for doc in documents:
    print(doc)