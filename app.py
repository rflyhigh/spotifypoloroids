from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
from datetime import datetime
import uuid
import json
import io
import zipfile
import base64
from database import init_db, get_db
from spotify_api import get_spotify_token, search_track
from models import save_polaroid, get_polaroid, get_polaroid_group, save_polaroid_group
import requests
from werkzeug.urls import url_parse

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
        # For PDF download, we'll redirect to client-side generation
        return redirect(url_for('view_group', group_id=group_id, download='pdf'))
    else:
        # Create a ZIP file in memory with the polaroid images
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for i, polaroid in enumerate(group['polaroids']):
                # Download the image from the URL
                try:
                    image_url = polaroid['track']['image']
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        # Save the album image
                        image_filename = f"polaroid_{i+1}_album.jpg"
                        zf.writestr(image_filename, image_response.content)
                        
                        # Save the metadata as JSON
                        metadata_filename = f"polaroid_{i+1}_metadata.json"
                        metadata = {
                            "track": polaroid['track'],
                            "customization": polaroid['customization']
                        }
                        zf.writestr(metadata_filename, json.dumps(metadata, indent=2))
                        
                        # Create a simple HTML representation
                        html_filename = f"polaroid_{i+1}.html"
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>{polaroid['track']['artist']} - {polaroid['track']['name']}</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; text-align: center; }}
                                .polaroid {{ 
                                    width: 300px; 
                                    padding: 15px 15px 30px; 
                                    background: {polaroid['customization'].get('backgroundColor', '#ffffff')};
                                    margin: 20px auto;
                                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                                }}
                                .polaroid img {{ width: 100%; height: auto; }}
                                .title {{ font-size: 18px; font-weight: bold; margin-top: 10px; }}
                                .artist {{ font-size: 16px; }}
                                .details {{ font-size: 14px; margin-top: 5px; }}
                            </style>
                        </head>
                        <body>
                            <div class="polaroid">
                                <img src="{image_filename}" alt="{polaroid['track']['name']}">
                                <div class="title">{polaroid['track']['name']}</div>
                                <div class="artist">{polaroid['track']['artist']}</div>
                                <div class="details">
                                    Album: {polaroid['track']['album']}<br>
                                    Year: {polaroid['track']['year']}
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        zf.writestr(html_filename, html_content)
                        
                except Exception as e:
                    print(f"Error processing polaroid {i+1}: {str(e)}")
                    continue
            
            # Add a README file
            readme_content = f"""
            Spotify Polaroid Collection: {group['name']}
            Created: {group['created_at']}
            
            This ZIP file contains {len(group['polaroids'])} polaroids.
            For each polaroid, you'll find:
            - The album image (polaroid_X_album.jpg)
            - The metadata in JSON format (polaroid_X_metadata.json)
            - A simple HTML representation (polaroid_X.html)
            
            To view the polaroids online, visit: {request.url_root.rstrip('/')}group/{group_id}
            """
            zf.writestr("README.txt", readme_content)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"polaroid_group_{group_id}.zip"
        )

@app.route('/check-font', methods=['POST'])
def check_font():
    font_url = request.json.get('fontUrl', '')
    
    if not font_url:
        return jsonify({"error": "No font URL provided"}), 400
    
    # Basic validation of the font URL
    parsed_url = url_parse(font_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return jsonify({"error": "Invalid URL format"}), 400
    
    # Check if URL ends with a font file extension
    valid_extensions = ['.ttf', '.otf', '.woff', '.woff2']
    has_valid_extension = any(font_url.lower().endswith(ext) for ext in valid_extensions)
    
    if not has_valid_extension:
        return jsonify({"error": "URL does not point to a valid font file"}), 400
    
    # Try to fetch the font to verify it exists
    try:
        response = requests.head(font_url, timeout=5)
        if response.status_code != 200:
            return jsonify({"error": f"Font URL returned status code {response.status_code}"}), 400
    except Exception as e:
        return jsonify({"error": f"Could not access font URL: {str(e)}"}), 400
    
    return jsonify({
        "success": True,
        "message": "Font URL is valid",
        "fontUrl": font_url
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
