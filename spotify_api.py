import requests
import base64

def get_spotify_token(client_id, client_secret):
    """Get an access token from Spotify API"""
    auth_string = f"{client_id}:{client_secret}"
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
    """Search for tracks using the Spotify API"""
    url = f"https://api.spotify.com/v1/search?q={track_name}&type=track&limit=10"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    json_result = response.json()
    
    if "tracks" in json_result and "items" in json_result["tracks"] and len(json_result["tracks"]["items"]) > 0:
        return json_result["tracks"]["items"]
    return []
