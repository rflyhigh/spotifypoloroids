from database import get_db
import uuid
from datetime import datetime

def save_polaroid(polaroid_data):
    """Save a single polaroid to the database"""
    db = get_db()
    polaroid_id = str(uuid.uuid4())
    
    # Create document to insert
    document = {
        "_id": polaroid_id,
        "data": polaroid_data,
        "created_at": datetime.now()
    }
    
    # Insert into MongoDB
    db.polaroids.insert_one(document)
    
    return polaroid_id

def get_polaroid(polaroid_id):
    """Retrieve a polaroid by ID"""
    db = get_db()
    polaroid = db.polaroids.find_one({"_id": polaroid_id})
    
    if polaroid:
        # Convert MongoDB document to a Python dict
        return {
            "id": polaroid["_id"],
            "data": polaroid["data"],
            "created_at": polaroid["created_at"].isoformat()
        }
    return None

def save_polaroid_group(group_name, polaroids_data):
    """Save a group of polaroids"""
    db = get_db()
    group_id = str(uuid.uuid4())
    
    # Create document to insert
    document = {
        "_id": group_id,
        "name": group_name,
        "polaroids": polaroids_data,
        "created_at": datetime.now()
    }
    
    # Insert into MongoDB
    db.polaroid_groups.insert_one(document)
    
    return group_id

def get_polaroid_group(group_id):
    """Retrieve a polaroid group by ID"""
    db = get_db()
    group = db.polaroid_groups.find_one({"_id": group_id})
    
    if group:
        # Convert MongoDB document to a Python dict
        return {
            "id": group["_id"],
            "name": group["name"],
            "polaroids": group["polaroids"],
            "created_at": group["created_at"].isoformat()
        }
    return None
