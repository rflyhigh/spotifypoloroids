from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import requests
import base64
import os
import json
import time
import uuid
from datetime import datetime

app = Flask(__name__)

# Get Spotify API credentials from environment variables
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# In-memory storage for polaroids (in a production app, use a database)
polaroids = {}

# HTML template as a string
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Polaroid Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #dcd7d3;
            color: #2d2b2c;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            letter-spacing: 2px;
            font-weight: 600;
        }

        header p {
            font-size: 1.2rem;
            opacity: 0.8;
        }

        .search-container {
            display: flex;
            justify-content: center;
            margin-bottom: 40px;
        }

        #search-input {
            width: 60%;
            padding: 12px 20px;
            font-size: 1rem;
            border: 1px solid #ccc;
            border-radius: 4px 0 0 4px;
            font-family: 'Montserrat', sans-serif;
        }

        #search-button {
            padding: 12px 24px;
            background-color: #2d2b2c;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 1rem;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
        }

        #search-button:hover {
            background-color: #1a1919;
        }

        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }

        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 4px solid #2d2b2c;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        .polaroid-demo {
            text-align: center;
            margin-top: 60px;
        }

        .polaroid-demo h2 {
            margin-bottom: 20px;
            font-size: 1.8rem;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .polaroid {
            background-color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 15px 15px 30px;
            display: inline-block;
            width: 736px; /* Exact width from reference */
            max-width: 100%;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .polaroid:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }

        .polaroid-content {
            display: flex;
            flex-direction: column;
        }

        .polaroid-image {
            width: 100%;
            height: auto;
            aspect-ratio: 1/1;
            overflow: hidden;
            margin-bottom: 15px;
            background-color: #f5f5f5;
        }

        .polaroid-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .polaroid-info {
            text-align: left;
            padding: 0 5px;
        }

        .polaroid-title {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }

        .polaroid-artist {
            font-size: 24px;
            margin-bottom: 10px;
            opacity: 0.8;
        }

        .polaroid-details {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 18px;
        }

        .polaroid-album {
            max-width: 70%;
        }

        .polaroid-year {
            font-weight: 500;
        }

        .polaroid-tracks {
            font-family: 'Roboto Mono', monospace;
            font-size: 16px;
            line-height: 1.4;
            opacity: 0.7;
            margin-top: 5px;
        }

        .result-item {
            cursor: pointer;
            transition: transform 0.3s;
            display: flex;
            justify-content: center;
        }

        .result-item:hover {
            transform: translateY(-5px);
        }

        .button-container {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }

        .download-btn, .share-btn {
            padding: 8px 16px;
            background-color: #2d2b2c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
            flex: 1;
            margin: 0 5px;
        }

        .download-btn:hover, .share-btn:hover {
            background-color: #1a1919;
        }
        
        .error, .no-results {
            text-align: center;
            font-size: 1.2rem;
            margin: 20px 0;
            color: #2d2b2c;
        }

        .share-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background-color: #dcd7d3;
            padding: 30px;
            border-radius: 8px;
            max-width: 500px;
            width: 90%;
            text-align: center;
        }

        .share-link {
            display: block;
            width: 100%;
            padding: 10px;
            margin: 15px 0;
            font-family: 'Roboto Mono', monospace;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }

        .share-options {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }

        .share-option {
            padding: 10px 15px;
            background-color: #2d2b2c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
        }

        .share-option:hover {
            background-color: #1a1919;
        }

        .close-modal {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 24px;
            color: white;
            cursor: pointer;
        }

        .home-hero {
            text-align: center;
            margin: 60px 0;
        }

        .home-hero h2 {
            font-size: 2rem;
            margin-bottom: 20px;
        }

        .home-hero p {
            font-size: 1.2rem;
            max-width: 800px;
            margin: 0 auto 30px;
        }

        .cta-button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #2d2b2c;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 1.1rem;
            transition: background-color 0.3s;
        }

        .cta-button:hover {
            background-color: #1a1919;
        }

        .polaroid-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 40px 0;
        }

        .shared-polaroid {
            max-width: 100%;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        @media (max-width: 768px) {
            #search-input {
                width: 70%;
            }
            
            .polaroid {
                width: 100%;
            }
            
            .button-container {
                flex-direction: column;
            }
            
            .download-btn, .share-btn {
                margin: 5px 0;
            }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>Spotify Polaroid Generator</h1>
            <p>Search for a song and create a beautiful polaroid-style image</p>
        </header>
        
        <div class="search-container">
            <input type="text" id="search-input" placeholder="Search for a song...">
            <button id="search-button">Search</button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
        </div>
        
        <div class="results-container" id="results-container">
            <!-- Search results will appear here -->
        </div>
        
        <div class="polaroid-demo">
            <h2>Polaroid Demo</h2>
            <div class="result-item">
                <div class="polaroid">
                    <div class="polaroid-content">
                        <div class="polaroid-image">
                            <img src="https://i.scdn.co/image/ab67616d0000b2731dacfbc31cc873d132958af9" alt="Demo Polaroid" crossorigin="anonymous">
                        </div>
                        <div class="polaroid-info">
                            <h3 class="polaroid-title">HEARTLESS</h3>
                            <p class="polaroid-artist">KANYE WEST</p>
                            <div class="polaroid-details">
                                <p class="polaroid-album">808s & Heartbreak</p>
                                <p class="polaroid-year">2008</p>
                            </div>
                            <div class="polaroid-tracks">
                                <p>808S. &.</p>
                                <p>HEARTBREAK.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Share Modal -->
    <div class="share-modal" id="share-modal">
        <span class="close-modal" id="close-modal">&times;</span>
        <div class="modal-content">
            <h2>Share Your Polaroid</h2>
            <p>Copy this link to share your polaroid:</p>
            <input type="text" id="share-link" class="share-link" readonly>
            <div class="share-options">
                <button class="share-option" id="copy-link">Copy Link</button>
                <button class="share-option" id="share-twitter">Twitter</button>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('search-input');
            const searchButton = document.getElementById('search-button');
            const loadingElement = document.getElementById('loading');
            const resultsContainer = document.getElementById('results-container');
            const shareModal = document.getElementById('share-modal');
            const shareLink = document.getElementById('share-link');
            const closeModal = document.getElementById('close-modal');
            const copyLinkBtn = document.getElementById('copy-link');
            const shareTwitterBtn = document.getElementById('share-twitter');
            
            searchButton.addEventListener('click', performSearch);
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            closeModal.addEventListener('click', function() {
                shareModal.style.display = 'none';
            });
            
            copyLinkBtn.addEventListener('click', function() {
                shareLink.select();
                document.execCommand('copy');
                alert('Link copied to clipboard!');
            });
            
            shareTwitterBtn.addEventListener('click', function() {
                const url = shareLink.value;
                const text = 'Check out this Spotify Polaroid I created!';
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
            });
            
            function performSearch() {
                const query = searchInput.value.trim();
                
                if (!query) {
                    alert('Please enter a search term');
                    return;
                }
                
                // Show loading spinner
                loadingElement.style.display = 'block';
                resultsContainer.innerHTML = '';
                
                // Send search request to backend
                fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query }),
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loading spinner
                    loadingElement.style.display = 'none';
                    
                    if (data.error) {
                        resultsContainer.innerHTML = `<p class="error">${data.error}</p>`;
                        return;
                    }
                    
                    if (!data.results || data.results.length === 0) {
                        resultsContainer.innerHTML = '<p class="no-results">No results found</p>';
                        return;
                    }
                    
                    // Display results
                    displayResults(data.results);
                })
                .catch(error => {
                    loadingElement.style.display = 'none';
                    resultsContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
                });
            }
            
            function displayResults(results) {
                resultsContainer.innerHTML = '';
                
                results.forEach(track => {
                    const polaroid = createPolaroid(track);
                    resultsContainer.appendChild(polaroid);
                });
            }
            
            function createPolaroid(track) {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                
                // Create track list from album name (for demonstration)
                const albumWords = track.album.split(' ');
                let trackList = '';
                
                if (albumWords.length > 1) {
                    const firstLine = albumWords.slice(0, Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                    const secondLine = albumWords.slice(Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                    trackList = `<p>${firstLine}</p><p>${secondLine}</p>`;
                } else {
                    trackList = `<p>${track.album.toUpperCase()}.</p>`;
                }
                
                resultItem.innerHTML = `
                    <div class="polaroid">
                        <div class="polaroid-content">
                            <div class="polaroid-image">
                                <img src="${track.image}" alt="${track.name}" crossorigin="anonymous">
                            </div>
                            <div class="polaroid-info">
                                <h3 class="polaroid-title">${track.name.toUpperCase()}</h3>
                                <p class="polaroid-artist">${track.artist.toUpperCase()}</p>
                                <div class="polaroid-details">
                                    <p class="polaroid-album">${track.album}</p>
                                    <p class="polaroid-year">${track.year}</p>
                                </div>
                                <div class="polaroid-tracks">
                                    ${trackList}
                                </div>
                            </div>
                        </div>
                        <div class="button-container">
                            <button class="download-btn" data-track='${JSON.stringify(track)}'>Download</button>
                            <button class="share-btn" data-track='${JSON.stringify(track)}'>Share</button>
                        </div>
                    </div>
                `;
                
                // Add download functionality
                const downloadBtn = resultItem.querySelector('.download-btn');
                downloadBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    generateAndDownloadImage(this.closest('.polaroid'), trackData);
                });
                
                // Add share functionality
                const shareBtn = resultItem.querySelector('.share-btn');
                shareBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    generateAndShareImage(this.closest('.polaroid'), trackData);
                });
                
                return resultItem;
            }
            
            function generateAndDownloadImage(polaroidElement, trackData) {
                // Create a clone of the polaroid for image generation
                const polaroidClone = polaroidElement.cloneNode(true);
                
                // Remove buttons from the clone
                const buttonContainer = polaroidClone.querySelector('.button-container');
                if (buttonContainer) {
                    buttonContainer.remove();
                }
                
                // Append the clone to the body temporarily (hidden)
                polaroidClone.style.position = 'absolute';
                polaroidClone.style.left = '-9999px';
                document.body.appendChild(polaroidClone);
                
                // Generate image from the clone
                html2canvas(polaroidClone, {
                    backgroundColor: 'white',
                    scale: 2,
                    logging: false,
                    useCORS: true, // Important for loading cross-origin images
                    allowTaint: false
                }).then(canvas => {
                    // Remove the clone
                    document.body.removeChild(polaroidClone);
                    
                    // Convert canvas to a downloadable image
                    const link = document.createElement('a');
                    link.download = `${trackData.artist} - ${trackData.name} Polaroid.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                }).catch(err => {
                    console.error("Error generating image:", err);
                    alert("Failed to generate downloadable image. Please try again.");
                    
                    // Clean up
                    if (document.body.contains(polaroidClone)) {
                        document.body.removeChild(polaroidClone);
                    }
                });
            }
            
            function generateAndShareImage(polaroidElement, trackData) {
                // Create a clone of the polaroid for image generation
                const polaroidClone = polaroidElement.cloneNode(true);
                
                // Remove buttons from the clone
                const buttonContainer = polaroidClone.querySelector('.button-container');
                if (buttonContainer) {
                    buttonContainer.remove();
                }
                
                // Append the clone to the body temporarily (hidden)
                polaroidClone.style.position = 'absolute';
                polaroidClone.style.left = '-9999px';
                document.body.appendChild(polaroidClone);
                
                // Generate image from the clone
                html2canvas(polaroidClone, {
                    backgroundColor: 'white',
                    scale: 2,
                    logging: false,
                    useCORS: true, // Important for loading cross-origin images
                    allowTaint: false
                }).then(canvas => {
                    // Remove the clone
                    document.body.removeChild(polaroidClone);
                    
                    // Get the image data URL
                    const imageData = canvas.toDataURL('image/png');
                    
                    // Save the polaroid to get a shareable link
                    fetch('/save-polaroid', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            trackData: trackData,
                            imageData: imageData
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert(`Error: ${data.error}`);
                            return;
                        }
                        
                        // Show the share modal with the link
                        shareLink.value = data.shareUrl;
                        shareModal.style.display = 'flex';
                    })
                    .catch(error => {
                        console.error("Error saving polaroid:", error);
                        alert("Failed to generate shareable link. Please try again.");
                    });
                }).catch(err => {
                    console.error("Error generating image:", err);
                    alert("Failed to generate shareable image. Please try again.");
                    
                    // Clean up
                    if (document.body.contains(polaroidClone)) {
                        document.body.removeChild(polaroidClone);
                    }
                });
            }
        });
    </script>
    
    <!-- Add html2canvas for image generation -->
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
</body>
</html>
"""

# Polaroid view template
POLAROID_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Polaroid - Shared Image</title>
    <meta property="og:title" content="Spotify Polaroid">
    <meta property="og:description" content="Check out this Spotify Polaroid I created!">
    <meta property="og:image" content="{{ image_url }}">
    <meta property="og:type" content="website">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #dcd7d3;
            color: #2d2b2c;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            letter-spacing: 2px;
            font-weight: 600;
        }

        header p {
            font-size: 1.2rem;
            opacity: 0.8;
        }

        header a {
            color: #2d2b2c;
            text-decoration: none;
            border-bottom: 1px solid #2d2b2c;
            transition: opacity 0.3s;
        }

        header a:hover {
            opacity: 0.7;
        }

        .polaroid-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 40px 0;
        }

        .shared-polaroid {
            max-width: 100%;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .cta-container {
            text-align: center;
            margin-top: 40px;
        }

        .cta-button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #2d2b2c;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 1.1rem;
            transition: background-color 0.3s;
        }

        .cta-button:hover {
            background-color: #1a1919;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>Spotify Polaroid</h1>
            <p><a href="/app">Create your own</a></p>
        </header>
        
        <div class="polaroid-container">
            <img src="{{ image_data }}" alt="Spotify Polaroid" class="shared-polaroid">
        </div>
        
        <div class="cta-container">
            <a href="/app" class="cta-button">Create Your Own Polaroid</a>
        </div>
    </div>
</body>
</html>
"""

def get_spotify_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
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
    url = f"https://api.spotify.com/v1/search?q={track_name}&type=track&limit=10"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    json_result = response.json()
    
    if "tracks" in json_result and "items" in json_result["tracks"] and len(json_result["tracks"]["items"]) > 0:
        return json_result["tracks"]["items"]
    return []

@app.route('/')
def home():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/app')
def app_page():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    if not CLIENT_ID or not CLIENT_SECRET:
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
def save_polaroid():
    data = request.json
    track_data = data.get('trackData')
    image_data = data.get('imageData')
    
    if not track_data or not image_data:
        return jsonify({"error": "Missing required data"}), 400
    
    # Generate a unique ID for the polaroid
    polaroid_id = str(uuid.uuid4())
    
    # Store the polaroid data
    polaroids[polaroid_id] = {
        "track_data": track_data,
        "image_data": image_data,
        "created_at": datetime.now().isoformat()
    }
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/polaroid/{polaroid_id}"
    
    return jsonify({
        "success": True,
        "id": polaroid_id,
        "shareUrl": share_url
    })

@app.route('/polaroid/<polaroid_id>')
def view_polaroid(polaroid_id):
    if polaroid_id not in polaroids:
        return "Polaroid not found", 404
    
    polaroid = polaroids[polaroid_id]
    image_data = polaroid["image_data"]
    image_url = request.url_root.rstrip('/') + f"/polaroid/{polaroid_id}/image"
    
    return render_template_string(
        POLAROID_TEMPLATE, 
        image_data=image_data,
        image_url=image_url
    )

@app.route('/polaroid/<polaroid_id>/image')
def get_polaroid_image(polaroid_id):
    if polaroid_id not in polaroids:
        return "Image not found", 404
    
    # Return the image data directly
    image_data = polaroids[polaroid_id]["image_data"]
    
    # Extract the base64 data part (remove the prefix)
    if ',' in image_data:
        image_data = image_data.split(',', 1)[1]
    
    image_binary = base64.b64decode(image_data)
    
    response = app.response_class(
        response=image_binary,
        status=200,
        mimetype='image/png'
    )
    
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
