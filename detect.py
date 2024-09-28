from pymongo import MongoClient
import datetime

def get_db_connection():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sen_net_db']
        return db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return None

def get_detected_data():
    db = get_db_connection()
    if db is None:
        return []
    collection = db['detected_issues']
    try:
        data = list(collection.find().sort('timestamp', -1))
        return [{"type": item['type'], "details": item['details'], "timestamp": item['timestamp']} for item in data]
    except Exception as e:
        print(f'Error fetching detected data: {e}')
        return []

def insert_detected_issue(issue_type, details):
    db = get_db_connection()
    if db is None:
        return
    collection = db['detected_issues']
    try:
        collection.insert_one({
            'type': issue_type,
            'details': details,
            'timestamp': datetime.datetime.now()
        })
    except Exception as e:
        print(f'Error inserting issue: {e}')

def clear_detected_data():
    db = get_db_connection()
    if db is None:
        return 0
    collection = db['detected_issues']
    try:
        result = collection.delete_many({})
        return result.deleted_count
    except Exception as e:
        print(f'Error clearing detected data: {e}')
        return 0
