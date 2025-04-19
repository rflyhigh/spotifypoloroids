from flask import Flask, render_template, request, jsonify
import requests
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Get Spotify API credentials from environment variables
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

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
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('index.html')

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

@app.route('/templates/index.html')
def serve_index_template():
    return """
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
        }

        .polaroid {
            background-color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 15px 15px 30px;
            display: inline-block;
            max-width: 400px;
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
            height: 300px;
            overflow: hidden;
            margin-bottom: 15px;
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
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 5px;
            letter-spacing: 1px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .polaroid-artist {
            font-size: 1.1rem;
            margin-bottom: 10px;
            opacity: 0.8;
        }

        .polaroid-details {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }

        .polaroid-album {
            max-width: 70%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .polaroid-year {
            font-weight: 500;
        }

        .polaroid-tracks {
            font-family: 'Roboto Mono', monospace;
            font-size: 0.8rem;
            line-height: 1.4;
            opacity: 0.7;
        }

        .result-item {
            cursor: pointer;
            transition: transform 0.3s;
        }

        .result-item:hover {
            transform: translateY(-5px);
        }

        .download-btn {
            display: block;
            margin-top: 15px;
            padding: 8px 16px;
            background-color: #2d2b2c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
        }

        .download-btn:hover {
            background-color: #1a1919;
        }
        
        .spotify-player {
            margin-top: 15px;
            width: 100%;
            height: 80px;
        }
        
        .error, .no-results {
            text-align: center;
            font-size: 1.2rem;
            margin: 20px 0;
            color: #2d2b2c;
        }

        @media (max-width: 768px) {
            #search-input {
                width: 70%;
            }
            
            .polaroid {
                max-width: 100%;
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
            <div class="polaroid">
                <div class="polaroid-content">
                    <div class="polaroid-image">
                        <img src="https://i.scdn.co/image/ab67616d0000b2731dacfbc31cc873d132958af9" alt="Demo Polaroid">
                    </div>
                    <div class="polaroid-info">
                        <h3 class="polaroid-title">SONG TITLE</h3>
                        <p class="polaroid-artist">ARTIST NAME</p>
                        <div class="polaroid-details">
                            <p class="polaroid-album">ALBUM NAME</p>
                            <p class="polaroid-year">2023</p>
                        </div>
                        <div class="polaroid-tracks">
                            <p>TRACK 1. TRACK 2. TRACK 3.</p>
                            <p>TRACK 4. TRACK 5. TRACK 6.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('search-input');
            const searchButton = document.getElementById('search-button');
            const loadingElement = document.getElementById('loading');
            const resultsContainer = document.getElementById('results-container');
            
            searchButton.addEventListener('click', performSearch);
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
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
                
                // Extract Spotify track ID from URI
                const spotifyTrackId = track.spotify_uri ? track.spotify_uri.split(':').pop() : '';
                
                resultItem.innerHTML = `
                    <div class="polaroid">
                        <div class="polaroid-content">
                            <div class="polaroid-image">
                                <img src="${track.image}" alt="${track.name}">
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
                            ${spotifyTrackId ? `
                            <iframe class="spotify-player" 
                                src="https://open.spotify.com/embed/track/${spotifyTrackId}" 
                                frameborder="0" 
                                allowtransparency="true" 
                                allow="encrypted-media">
                            </iframe>
                            ` : ''}
                        </div>
                        <button class="download-btn" data-track='${JSON.stringify(track)}'>Download Polaroid</button>
                    </div>
                `;
                
                // Add download functionality
                const downloadBtn = resultItem.querySelector('.download-btn');
                downloadBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    
                    // Create a canvas from the polaroid for download
                    html2canvas(this.parentElement, {
                        backgroundColor: null,
                        scale: 2,
                        logging: false,
                        // Exclude the player and button from the image
                        onclone: function(clonedDoc) {
                            const clonedPolaroid = clonedDoc.querySelector('.polaroid');
                            const playerToRemove = clonedPolaroid.querySelector('.spotify-player');
                            const buttonToRemove = clonedPolaroid.querySelector('.download-btn');
                            
                            if (playerToRemove) playerToRemove.remove();
                            if (buttonToRemove) buttonToRemove.remove();
                        }
                    }).then(canvas => {
                        // Convert canvas to a downloadable image
                        const link = document.createElement('a');
                        link.download = `${trackData.artist} - ${trackData.name} Polaroid.png`;
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                    }).catch(err => {
                        console.error("Error generating image:", err);
                        alert("Failed to generate downloadable image. Please try again.");
                    });
                });
                
                return resultItem;
            }
        });
    </script>
    
    <!-- Add html2canvas for download functionality -->
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
</body>
</html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
