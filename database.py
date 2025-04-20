from pymongo import MongoClient
import os

_db = None

def init_db():
    global _db
    mongo_uri = os.environ.get("MONGODB_URI")
    client = MongoClient(mongo_uri)
    _db = client.polaroid_app
    
def get_db():
    global _db
    if _db is None:
        init_db()
    return _db
