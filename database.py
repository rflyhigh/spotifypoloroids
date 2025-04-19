import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from config import Config

# Connect to MongoDB
client = MongoClient(Config.MONGODB_URI)
db = client.get_database("sonroids")

# Collections
polaroids_collection = db.polaroids
groups_collection = db.groups

# Polaroid functions
def save_polaroid(track_data, image_data, customization):
    """Save a polaroid to the database and return its ID"""
    polaroid_data = {
        "track_data": track_data,
        "image_data": image_data,
        "customization": customization,
        "created_at": datetime.datetime.utcnow()
    }
    
    result = polaroids_collection.insert_one(polaroid_data)
    return str(result.inserted_id)

def get_polaroid(polaroid_id):
    """Get a polaroid by its ID"""
    try:
        return polaroids_collection.find_one({"_id": ObjectId(polaroid_id)})
    except:
        return None

# Group functions
def save_group(name, items):
    """Save a group to the database and return its ID"""
    group_data = {
        "name": name,
        "items": items,
        "created_at": datetime.datetime.utcnow()
    }
    
    result = groups_collection.insert_one(group_data)
    return str(result.inserted_id)

def get_group(group_id):
    """Get a group by its ID"""
    try:
        return groups_collection.find_one({"_id": ObjectId(group_id)})
    except:
        return None

def get_all_groups():
    """Get all groups"""
    return list(groups_collection.find().sort("created_at", pymongo.DESCENDING))
