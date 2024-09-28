from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize SocketIO
socketio = SocketIO(app)

# Initialize MongoDB connection
def get_db_connection():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sen_net_db']
        return db
    except Exception as e:
        app.logger.error(f"MongoDB connection error: {e}")
        return None

from . import main  # Import the main module, ensuring routes are registered
