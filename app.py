from flask import Flask, render_template_string, request, jsonify
import requests
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Get Spotify API credentials from environment variables
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

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
            width: 100%;
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

        .modal-image {
            max-width: 100%;
            margin-bottom: 20px;
            border: 10px solid white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
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

        @media (max-width: 768px) {
            #search-input {
                width: 70%;
            }
            
            .polaroid {
                max-width: 100%;
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
                            <img src="https://i.scdn.co/image/ab67616d0000b2731dacfbc31cc873d132958af9" alt="Demo Polaroid">
                        </div>
                        <div class="polaroid-info">
                            <h3 class="polaroid-title">808S & HEARTBREAK</h3>
                            <p class="polaroid-artist">KANYE WEST</p>
                            <div class="polaroid-details">
                                <p class="polaroid-album">808s & Heartbreak</p>
                                <p class="polaroid-year">2008</p>
                            </div>
                            <div class="polaroid-tracks">
                                <p>SAY YOU WILL. WELCOME TO HEARTBREAK.</p>
                                <p>HEARTLESS. AMAZING. LOVE LOCKDOWN.</p>
                                <p>PARANOID. ROBOCOP. STREET LIGHTS.</p>
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
            <img id="modal-image" class="modal-image" src="" alt="Polaroid to share">
            <p>Share this polaroid with your friends:</p>
            <div class="share-options">
                <button class="share-option" id="copy-link">Copy Link</button>
                <button class="share-option" id="download-image">Download</button>
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
            const modalImage = document.getElementById('modal-image');
            const closeModal = document.getElementById('close-modal');
            const copyLink = document.getElementById('copy-link');
            const downloadImage = document.getElementById('download-image');
            const shareTwitter = document.getElementById('share-twitter');
            
            let currentImageUrl = '';
            
            searchButton.addEventListener('click', performSearch);
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            closeModal.addEventListener('click', function() {
                shareModal.style.display = 'none';
            });
            
            copyLink.addEventListener('click', function() {
                navigator.clipboard.writeText(currentImageUrl)
                    .then(() => {
                        alert('Link copied to clipboard!');
                    })
                    .catch(err => {
                        console.error('Failed to copy link: ', err);
                    });
            });
            
            downloadImage.addEventListener('click', function() {
                const link = document.createElement('a');
                link.href = currentImageUrl;
                link.download = 'spotify-polaroid.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
            
            shareTwitter.addEventListener('click', function() {
                const text = 'Check out this Spotify Polaroid I created!';
                const url = encodeURIComponent(currentImageUrl);
                window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
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
                    backgroundColor: null,
                    scale: 2,
                    logging: false
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
                    backgroundColor: null,
                    scale: 2,
                    logging: false
                }).then(canvas => {
                    // Remove the clone
                    document.body.removeChild(polaroidClone);
                    
                    // Set the image in the modal
                    const imageUrl = canvas.toDataURL('image/png');
                    currentImageUrl = imageUrl;
                    modalImage.src = imageUrl;
                    
                    // Show the modal
                    shareModal.style.display = 'flex';
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
