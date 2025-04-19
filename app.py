from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import json
import uuid
import io
from datetime import datetime
from PIL import Image
import tempfile
import threading
import time
import requests

from config import Config
from database import save_polaroid, get_polaroid, save_group, get_group, get_all_groups
from utils import get_spotify_token, search_track, create_track_list, start_ping_service

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for the self-ping mechanism"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    if not Config.SPOTIFY_CLIENT_ID or not Config.SPOTIFY_CLIENT_SECRET:
        return jsonify({"error": "Spotify API credentials not configured"}), 500
    
    token = get_spotify_token()
    results = search_track(query, token)
    
    tracks_data = []
    for track in results:
        album = track.get("album", {})
        artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
        release_date = album.get("release_date", "")
        
        # Format release date to just get the year
        try:
            if len(release_date) >= 4:  # At least has a year
                year = release_date[:4]
            else:
                year = "Unknown"
        except:
            year = "Unknown"
            
        image_url = album.get("images", [{}])[0].get("url") if album.get("images") else ""
        
        track_data = {
            "id": track.get("id"),
            "name": track.get("name"),
            "artist": artists,
            "album": album.get("name", ""),
            "year": year,
            "image": image_url,
            "preview_url": track.get("preview_url"),
            "spotify_uri": track.get("uri")
        }
        tracks_data.append(track_data)
    
    return jsonify({"results": tracks_data})

@app.route('/save-polaroid', methods=['POST'])
def save_polaroid_route():
    data = request.json
    track_data = data.get('trackData')
    image_data = data.get('imageData')
    customization = data.get('customization', {})
    
    if not track_data or not image_data:
        return jsonify({"error": "Missing required data"}), 400
    
    # Save to database
    polaroid_id = save_polaroid(track_data, image_data, customization)
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/polaroid/{polaroid_id}"
    
    return jsonify({
        "success": True,
        "id": polaroid_id,
        "shareUrl": share_url
    })

@app.route('/save-group', methods=['POST'])
def save_group_route():
    data = request.json
    group_name = data.get('name')
    items = data.get('items', [])
    
    if not group_name or not items:
        return jsonify({"error": "Missing required data"}), 400
    
    # Save to database
    group_id = save_group(group_name, items)
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/group/{group_id}"
    
    return jsonify({
        "success": True,
        "id": group_id,
        "shareUrl": share_url
    })

@app.route('/polaroid/<polaroid_id>')
def view_polaroid(polaroid_id):
    polaroid = get_polaroid(polaroid_id)
    
    if not polaroid:
        return "Polaroid not found", 404
    
    return render_template(
        'polaroid.html',
        image_data=polaroid["image_data"],
        track_data=polaroid["track_data"]
    )

@app.route('/group/<group_id>')
def view_group(group_id):
    group = get_group(group_id)
    
    if not group:
        return "Group not found", 404
    
    group_name = group["name"]
    items = group["items"]
    
    # Process items for template
    processed_items = []
    for item in items:
        track = item["track"]
        customization = item.get("customization", {
            "width": 350,
            "padding": 15,
            "bgColor": "#ffffff",
            "textColor": "#2d2b2c",
            "fontFamily": "Montserrat",
            "titleSize": 24,
            "artistSize": 18,
            "detailsSize": 14,
            "tracksSize": 12
        })
        
        track_list = create_track_list(track["album"])
        
        processed_items.append({
            "track": track,
            "customization": customization,
            "track_list": track_list
        })
    
    return render_template(
        'group.html',
        group_name=group_name,
        group_id=group_id,
        items=processed_items,
        item_count=len(items)
    )

@app.route('/export-images/<group_id>')
def export_images(group_id):
    group = get_group(group_id)
    
    if not group:
        return "Group not found", 404
    
    # In a real implementation, you would generate a zip file with all images
    # For now, we'll just redirect back to the group page
    return redirect(url_for('view_group', group_id=group_id))

@app.route('/export-pdf/<group_id>')
def export_pdf(group_id):
    group = get_group(group_id)
    
    if not group:
        return "Group not found", 404
    
    # In a real implementation, you would generate a PDF with all polaroids
    # For now, we'll just redirect back to the group page
    return redirect(url_for('view_group', group_id=group_id))

if __name__ == '__main__':
    # Start the self-ping service
    ping_thread = start_ping_service(app)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
