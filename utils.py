import requests
import base64
import threading
import time
from config import Config

def get_spotify_token():
    """Get a Spotify API access token"""
    auth_string = f"{Config.SPOTIFY_CLIENT_ID}:{Config.SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    json_result = response.json()
    
    return json_result.get("access_token")

def search_track(track_name, token):
    """Search for tracks on Spotify"""
    url = f"https://api.spotify.com/v1/search?q={track_name}&type=track&limit=10"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    json_result = response.json()
    
    if "tracks" in json_result and "items" in json_result["tracks"] and len(json_result["tracks"]["items"]) > 0:
        return json_result["tracks"]["items"]
    return []

def create_track_list(album_name):
    """Create a stylized track list from an album name"""
    album_words = album_name.split(' ')
    track_list = []
    
    if len(album_words) > 1:
        first_line = album_words[:len(album_words)//2]
        second_line = album_words[len(album_words)//2:]
        
        track_list.append('. '.join(first_line).upper() + '.')
        track_list.append('. '.join(second_line).upper() + '.')
    else:
        track_list.append(album_name.upper() + '.')
    
    return track_list

def start_ping_service(app):
    """Start a background thread to ping the app regularly"""
    def ping_app():
        while True:
            try:
                requests.get(f"{Config.APP_URL}/health")
                print(f"Pinged {Config.APP_URL}/health at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                print(f"Ping failed: {e}")
            
            time.sleep(Config.PING_INTERVAL)
    
    ping_thread = threading.Thread(target=ping_app, daemon=True)
    ping_thread.start()
    
    return ping_thread
