from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
from datetime import datetime
import uuid
import json
import io
import zipfile
from database import init_db, get_db
from spotify_api import get_spotify_token, search_track
from models import save_polaroid, get_polaroid, get_polaroid_group, save_polaroid_group

app = Flask(__name__)

# Initialize MongoDB connection
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        return jsonify({"error": "Spotify API credentials not configured"}), 500
    
    token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)
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
    polaroid_data = data.get('polaroidData')
    
    if not polaroid_data:
        return jsonify({"error": "Missing required data"}), 400
    
    # Save the polaroid data to MongoDB
    polaroid_id = save_polaroid(polaroid_data)
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/polaroid/{polaroid_id}"
    
    return jsonify({
        "success": True,
        "id": polaroid_id,
        "shareUrl": share_url
    })

@app.route('/save-polaroid-group', methods=['POST'])
def save_polaroid_group_route():
    data = request.json
    group_name = data.get('groupName', 'My Polaroid Group')
    polaroids_data = data.get('polaroids', [])
    
    if not polaroids_data:
        return jsonify({"error": "No polaroids provided"}), 400
    
    # Save the polaroid group to MongoDB
    group_id = save_polaroid_group(group_name, polaroids_data)
    
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
    
    return render_template('polaroid_view.html', polaroid=polaroid)

@app.route('/group/<group_id>')
def view_group(group_id):
    group = get_polaroid_group(group_id)
    if not group:
        return "Polaroid group not found", 404
    
    return render_template('group_view.html', group=group)

@app.route('/download-group/<group_id>')
def download_group(group_id):
    format_type = request.args.get('format', 'zip')
    group = get_polaroid_group(group_id)
    
    if not group:
        return "Polaroid group not found", 404
    
    if format_type == 'pdf':
        return "PDF download not implemented yet", 501
    else:
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for i, polaroid in enumerate(group['polaroids']):
                polaroid_data = json.dumps(polaroid).encode('utf-8')
                zf.writestr(f"polaroid_{i+1}.json", polaroid_data)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"polaroid_group_{group_id}.zip"
        )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
