import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Spotify API credentials
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
    # MongoDB connection
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/sonroids")
    
    # App settings
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))
    
    # Self-ping settings
    APP_URL = os.environ.get("APP_URL", "https://spotifypoloroids.onrender.com")
    PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 600))  # 10 minutes in seconds
