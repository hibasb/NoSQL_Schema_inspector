from connector import get_connection, get_collection, get_documents
from schema_inferrer import infer_schema, display_schema

client = get_connection()
collection = get_collection(client, "nosql_inspector_db", "employees")
documents = get_documents(collection)

schema = infer_schema(documents)
display_schema(schema)