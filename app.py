from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
import requests
import base64
import os
import json
import time
import uuid
import io
from datetime import datetime
from PIL import Image
import tempfile

app = Flask(__name__)

# Get Spotify API credentials from environment variables
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# In-memory storage (in a production app, use a database)
polaroids = {}
groups = {}

# HTML templates as strings
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sonroids - Spotify Polaroid Generator</title>
    <style>
        :root {
            --bg-color: #dcd7d3;
            --text-color: #2d2b2c;
            --accent-color: #2d2b2c;
            --card-color: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
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
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 1rem;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
        }

        #search-button:hover {
            opacity: 0.9;
        }

        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }

        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 4px solid var(--accent-color);
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
            background-color: var(--card-color);
            box-shadow: 0 4px 8px var(--shadow-color);
            padding: 15px 15px 30px;
            display: inline-block;
            width: 350px; /* Default width */
            max-width: 100%;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .polaroid:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 16px var(--shadow-color);
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
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }

        .polaroid-artist {
            font-size: 18px;
            margin-bottom: 10px;
            opacity: 0.8;
        }

        .polaroid-details {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .polaroid-album {
            max-width: 70%;
        }

        .polaroid-year {
            font-weight: 500;
        }

        .polaroid-tracks {
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
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

        .download-btn, .share-btn, .customize-btn, .add-to-group-btn {
            padding: 8px 16px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
            flex: 1;
            margin: 0 5px;
            font-size: 0.9rem;
        }

        .download-btn:hover, .share-btn:hover, .customize-btn:hover, .add-to-group-btn:hover {
            opacity: 0.9;
        }
        
        .error, .no-results {
            text-align: center;
            font-size: 1.2rem;
            margin: 20px 0;
            color: var(--text-color);
        }

        .modal {
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
            overflow-y: auto;
        }

        .modal-content {
            background-color: var(--bg-color);
            padding: 30px;
            border-radius: 8px;
            max-width: 800px;
            width: 90%;
            text-align: center;
            max-height: 90vh;
            overflow-y: auto;
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
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.3s;
        }

        .share-option:hover {
            opacity: 0.9;
        }

        .close-modal {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 24px;
            color: white;
            cursor: pointer;
        }

        .customizer-form {
            text-align: left;
            margin-top: 20px;
        }

        .customizer-form h3 {
            margin-bottom: 15px;
            text-align: center;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }

        .form-group input, .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: 'Montserrat', sans-serif;
        }

        .color-options {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 5px;
        }

        .color-option {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            border: 2px solid transparent;
        }

        .color-option.selected {
            border-color: var(--accent-color);
        }

        .font-options {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 5px;
        }

        .font-option {
            padding: 5px 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
            background-color: white;
        }

        .font-option.selected {
            background-color: var(--accent-color);
            color: white;
        }

        .apply-btn {
            display: block;
            width: 100%;
            padding: 10px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            margin-top: 20px;
            font-size: 1rem;
        }

        .apply-btn:hover {
            opacity: 0.9;
        }

        .group-container {
            margin-top: 40px;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }

        .group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .group-title {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .group-actions {
            display: flex;
            gap: 10px;
        }

        .group-btn {
            padding: 8px 16px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
        }

        .group-btn:hover {
            opacity: 0.9;
        }

        .group-items {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }

        .group-item {
            position: relative;
        }

        .remove-from-group {
            position: absolute;
            top: 5px;
            right: 5px;
            width: 24px;
            height: 24px;
            background-color: rgba(255, 0, 0, 0.7);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 14px;
        }

        .group-name-input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: 'Montserrat', sans-serif;
        }

        .export-options {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }

        .export-option {
            padding: 10px 15px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
        }

        .export-option:hover {
            opacity: 0.9;
        }

        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }

        .tab {
            padding: 10px 20px;
            background-color: rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            font-size: 1rem;
            transition: background-color 0.3s;
        }

        .tab.active {
            background-color: var(--accent-color);
            color: white;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        @media (max-width: 768px) {
            #search-input {
                width: 70%;
            }
            
            .polaroid {
                width: 100%;
                max-width: 350px;
            }
            
            .button-container {
                flex-direction: column;
            }
            
            .download-btn, .share-btn, .customize-btn, .add-to-group-btn {
                margin: 5px 0;
            }
            
            .modal-content {
                width: 95%;
                padding: 15px;
            }
            
            .group-items {
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>Sonroids</h1>
            <p>Create beautiful customizable polaroids from Spotify tracks</p>
        </header>
        
        <div class="tabs">
            <button class="tab active" data-tab="search">Search & Create</button>
            <button class="tab" data-tab="groups">My Groups</button>
        </div>
        
        <div class="tab-content active" id="search-tab">
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
        
        <div class="tab-content" id="groups-tab">
            <div class="group-container" id="group-container">
                <div class="group-header">
                    <h2 class="group-title">My Polaroid Groups</h2>
                    <div class="group-actions">
                        <button class="group-btn" id="create-group-btn">Create New Group</button>
                        <button class="group-btn" id="manage-groups-btn">Manage Groups</button>
                    </div>
                </div>
                <div id="groups-list">
                    <!-- Groups will be listed here -->
                    <p class="no-groups">You haven't created any groups yet. Add polaroids to a group from the search tab.</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Share Modal -->
    <div class="modal" id="share-modal">
        <span class="close-modal" id="close-share-modal">&times;</span>
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
    
    <!-- Customize Modal -->
    <div class="modal" id="customize-modal">
        <span class="close-modal" id="close-customize-modal">&times;</span>
        <div class="modal-content">
            <h2>Customize Your Polaroid</h2>
            <div class="customizer-form">
                <div class="form-group">
                    <label for="card-width">Card Width (px)</label>
                    <input type="number" id="card-width" min="200" max="800" value="350">
                </div>
                
                <div class="form-group">
                    <label for="card-padding">Card Padding (px)</label>
                    <input type="number" id="card-padding" min="5" max="50" value="15">
                </div>
                
                <div class="form-group">
                    <label>Background Color</label>
                    <div class="color-options" id="bg-color-options">
                        <div class="color-option selected" style="background-color: #ffffff;" data-color="#ffffff"></div>
                        <div class="color-option" style="background-color: #f8e9e9;" data-color="#f8e9e9"></div>
                        <div class="color-option" style="background-color: #e9f8f8;" data-color="#e9f8f8"></div>
                        <div class="color-option" style="background-color: #f8f8e9;" data-color="#f8f8e9"></div>
                        <div class="color-option" style="background-color: #e9e9f8;" data-color="#e9e9f8"></div>
                        <div class="color-option" style="background-color: #f8e9f8;" data-color="#f8e9f8"></div>
                    </div>
                    <input type="color" id="custom-bg-color" value="#ffffff">
                </div>
                
                <div class="form-group">
                    <label>Text Color</label>
                    <div class="color-options" id="text-color-options">
                        <div class="color-option selected" style="background-color: #2d2b2c;" data-color="#2d2b2c"></div>
                        <div class="color-option" style="background-color: #4a4a4a;" data-color="#4a4a4a"></div>
                        <div class="color-option" style="background-color: #6d6d6d;" data-color="#6d6d6d"></div>
                        <div class="color-option" style="background-color: #0f3460;" data-color="#0f3460"></div>
                        <div class="color-option" style="background-color: #541690;" data-color="#541690"></div>
                        <div class="color-option" style="background-color: #443C68;" data-color="#443C68"></div>
                    </div>
                    <input type="color" id="custom-text-color" value="#2d2b2c">
                </div>
                
                <div class="form-group">
                    <label>Font Family</label>
                    <div class="font-options" id="font-options">
                        <div class="font-option selected" data-font="Montserrat" style="font-family: 'Montserrat';">Montserrat</div>
                        <div class="font-option" data-font="Roboto Mono" style="font-family: 'Roboto Mono';">Roboto Mono</div>
                        <div class="font-option" data-font="Playfair Display" style="font-family: 'Playfair Display';">Playfair</div>
                        <div class="font-option" data-font="Poppins" style="font-family: 'Poppins';">Poppins</div>
                        <div class="font-option" data-font="Lora" style="font-family: 'Lora';">Lora</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="custom-font-url">Custom Font URL (Google Fonts)</label>
                    <input type="text" id="custom-font-url" placeholder="https://fonts.googleapis.com/css2?family=...">
                </div>
                
                <div class="form-group">
                    <label for="custom-font-name">Custom Font Name</label>
                    <input type="text" id="custom-font-name" placeholder="Font Name">
                </div>
                
                <div class="form-group">
                    <label for="title-size">Title Size (px)</label>
                    <input type="number" id="title-size" min="12" max="48" value="24">
                </div>
                
                <div class="form-group">
                    <label for="artist-size">Artist Size (px)</label>
                    <input type="number" id="artist-size" min="10" max="36" value="18">
                </div>
                
                <div class="form-group">
                    <label for="details-size">Details Size (px)</label>
                    <input type="number" id="details-size" min="8" max="24" value="14">
                </div>
                
                <div class="form-group">
                    <label for="tracks-size">Tracks Size (px)</label>
                    <input type="number" id="tracks-size" min="8" max="20" value="12">
                </div>
                
                <button class="apply-btn" id="apply-customization">Apply Changes</button>
            </div>
        </div>
    </div>
    
    <!-- Group Modal -->
    <div class="modal" id="group-modal">
        <span class="close-modal" id="close-group-modal">&times;</span>
        <div class="modal-content">
            <h2>Create or Add to Group</h2>
            <input type="text" id="group-name" class="group-name-input" placeholder="Enter group name...">
            <div id="existing-groups">
                <!-- Existing groups will be listed here -->
            </div>
            <button class="apply-btn" id="add-to-group-confirm">Add to Group</button>
        </div>
    </div>
    
    <!-- Group Share Modal -->
    <div class="modal" id="group-share-modal">
        <span class="close-modal" id="close-group-share-modal">&times;</span>
        <div class="modal-content">
            <h2>Share Your Polaroid Group</h2>
            <p>Copy this link to share your group:</p>
            <input type="text" id="group-share-link" class="share-link" readonly>
            <div class="share-options">
                <button class="share-option" id="copy-group-link">Copy Link</button>
                <button class="share-option" id="share-group-twitter">Twitter</button>
            </div>
        </div>
    </div>
    
    <!-- Export Group Modal -->
    <div class="modal" id="export-modal">
        <span class="close-modal" id="close-export-modal">&times;</span>
        <div class="modal-content">
            <h2>Export Your Polaroid Group</h2>
            <p>Choose how you want to export your group:</p>
            <div class="export-options">
                <button class="export-option" id="export-images">Download as Images</button>
                <button class="export-option" id="export-pdf">Download as PDF</button>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Elements
            const searchInput = document.getElementById('search-input');
            const searchButton = document.getElementById('search-button');
            const loadingElement = document.getElementById('loading');
            const resultsContainer = document.getElementById('results-container');
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            // Modals
            const shareModal = document.getElementById('share-modal');
            const shareLink = document.getElementById('share-link');
            const closeShareModal = document.getElementById('close-share-modal');
            const copyLinkBtn = document.getElementById('copy-link');
            const shareTwitterBtn = document.getElementById('share-twitter');
            
            const customizeModal = document.getElementById('customize-modal');
            const closeCustomizeModal = document.getElementById('close-customize-modal');
            const applyCustomizationBtn = document.getElementById('apply-customization');
            
            const groupModal = document.getElementById('group-modal');
            const closeGroupModal = document.getElementById('close-group-modal');
            const addToGroupConfirmBtn = document.getElementById('add-to-group-confirm');
            
            const groupShareModal = document.getElementById('group-share-modal');
            const groupShareLink = document.getElementById('group-share-link');
            const closeGroupShareModal = document.getElementById('close-group-share-modal');
            const copyGroupLinkBtn = document.getElementById('copy-group-link');
            const shareGroupTwitterBtn = document.getElementById('share-group-twitter');
            
            const exportModal = document.getElementById('export-modal');
            const closeExportModal = document.getElementById('close-export-modal');
            const exportImagesBtn = document.getElementById('export-images');
            const exportPdfBtn = document.getElementById('export-pdf');
            
            // Group management
            const createGroupBtn = document.getElementById('create-group-btn');
            const manageGroupsBtn = document.getElementById('manage-groups-btn');
            const groupsList = document.getElementById('groups-list');
            
            // State
            let currentPolaroid = null;
            let currentCustomization = {
                width: 350,
                padding: 15,
                bgColor: '#ffffff',
                textColor: '#2d2b2c',
                fontFamily: 'Montserrat',
                titleSize: 24,
                artistSize: 18,
                detailsSize: 14,
                tracksSize: 12
            };
            
            let groups = JSON.parse(localStorage.getItem('sonroids-groups') || '{}');
            
            // Tab switching
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabId = tab.getAttribute('data-tab');
                    
                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Show corresponding content
                    tabContents.forEach(content => {
                        content.classList.remove('active');
                        if (content.id === `${tabId}-tab`) {
                            content.classList.add('active');
                        }
                    });
                    
                    // If switching to groups tab, refresh the groups list
                    if (tabId === 'groups') {
                        renderGroups();
                    }
                });
            });
            
            // Event listeners
            searchButton.addEventListener('click', performSearch);
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            closeShareModal.addEventListener('click', function() {
                shareModal.style.display = 'none';
            });
            
            copyLinkBtn.addEventListener('click', function() {
                shareLink.select();
                document.execCommand('copy');
                alert('Link copied to clipboard!');
            });
            
            shareTwitterBtn.addEventListener('click', function() {
                const url = shareLink.value;
                const text = 'Check out this Sonroid I created!';
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
            });
            
            closeCustomizeModal.addEventListener('click', function() {
                customizeModal.style.display = 'none';
            });
            
            applyCustomizationBtn.addEventListener('click', function() {
                applyCustomization();
                customizeModal.style.display = 'none';
            });
            
            closeGroupModal.addEventListener('click', function() {
                groupModal.style.display = 'none';
            });
            
            addToGroupConfirmBtn.addEventListener('click', function() {
                addToGroup();
                groupModal.style.display = 'none';
            });
            
            closeGroupShareModal.addEventListener('click', function() {
                groupShareModal.style.display = 'none';
            });
            
            copyGroupLinkBtn.addEventListener('click', function() {
                groupShareLink.select();
                document.execCommand('copy');
                alert('Link copied to clipboard!');
            });
            
            shareGroupTwitterBtn.addEventListener('click', function() {
                const url = groupShareLink.value;
                const text = 'Check out this Sonroids group I created!';
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
            });
            
            closeExportModal.addEventListener('click', function() {
                exportModal.style.display = 'none';
            });
            
            exportImagesBtn.addEventListener('click', function() {
                exportImages();
                exportModal.style.display = 'none';
            });
            
            exportPdfBtn.addEventListener('click', function() {
                exportPdf();
                exportModal.style.display = 'none';
            });
            
            createGroupBtn.addEventListener('click', function() {
                showCreateGroupModal();
            });
            
            manageGroupsBtn.addEventListener('click', function() {
                // Show management interface
                alert('Use the groups tab to manage your groups. You can share, export, or delete groups.');
            });
            
            // Color option selection
            document.querySelectorAll('.color-option').forEach(option => {
                option.addEventListener('click', function() {
                    const colorType = this.parentElement.id === 'bg-color-options' ? 'bg' : 'text';
                    const color = this.getAttribute('data-color');
                    
                    // Update selected state
                    this.parentElement.querySelectorAll('.color-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    this.classList.add('selected');
                    
                    // Update color input
                    if (colorType === 'bg') {
                        document.getElementById('custom-bg-color').value = color;
                    } else {
                        document.getElementById('custom-text-color').value = color;
                    }
                });
            });
            
            // Font option selection
            document.querySelectorAll('.font-option').forEach(option => {
                option.addEventListener('click', function() {
                    const font = this.getAttribute('data-font');
                    
                    // Update selected state
                    document.querySelectorAll('.font-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    this.classList.add('selected');
                });
            });
            
            // Functions
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
                    <div class="polaroid" style="width: ${currentCustomization.width}px; padding: ${currentCustomization.padding}px ${currentCustomization.padding}px ${currentCustomization.padding * 2}px; background-color: ${currentCustomization.bgColor}; color: ${currentCustomization.textColor}; font-family: '${currentCustomization.fontFamily}', sans-serif;">
                        <div class="polaroid-content">
                            <div class="polaroid-image">
                                <img src="${track.image}" alt="${track.name}" crossorigin="anonymous">
                            </div>
                            <div class="polaroid-info">
                                <h3 class="polaroid-title" style="font-size: ${currentCustomization.titleSize}px;">${track.name.toUpperCase()}</h3>
                                <p class="polaroid-artist" style="font-size: ${currentCustomization.artistSize}px;">${track.artist.toUpperCase()}</p>
                                <div class="polaroid-details" style="font-size: ${currentCustomization.detailsSize}px;">
                                    <p class="polaroid-album">${track.album}</p>
                                    <p class="polaroid-year">${track.year}</p>
                                </div>
                                <div class="polaroid-tracks" style="font-size: ${currentCustomization.tracksSize}px;">
                                    ${trackList}
                                </div>
                            </div>
                        </div>
                        <div class="button-container">
                            <button class="download-btn" data-track='${JSON.stringify(track)}'>Download</button>
                            <button class="customize-btn" data-track='${JSON.stringify(track)}'>Customize</button>
                            <button class="add-to-group-btn" data-track='${JSON.stringify(track)}'>Add to Group</button>
                        </div>
                    </div>
                `;
                
                // Add download functionality
                const downloadBtn = resultItem.querySelector('.download-btn');
                downloadBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    generateAndDownloadImage(this.closest('.polaroid'), trackData);
                });
                
                // Add customize functionality
                const customizeBtn = resultItem.querySelector('.customize-btn');
                customizeBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    currentPolaroid = {
                        element: this.closest('.polaroid'),
                        track: trackData
                    };
                    showCustomizeModal();
                });
                
                // Add to group functionality
                const addToGroupBtn = resultItem.querySelector('.add-to-group-btn');
                addToGroupBtn.addEventListener('click', function() {
                    const trackData = JSON.parse(this.getAttribute('data-track'));
                    currentPolaroid = {
                        element: this.closest('.polaroid'),
                        track: trackData,
                        customization: { ...currentCustomization }
                    };
                    showGroupModal();
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
                    logging: false,
                    useCORS: true, // Important for loading cross-origin images
                    allowTaint: false
                }).then(canvas => {
                    // Remove the clone
                    document.body.removeChild(polaroidClone);
                    
                    // Convert canvas to a downloadable image
                    const link = document.createElement('a');
                    link.download = `${trackData.artist} - ${trackData.name} Sonroid.png`;
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
            
            function showCustomizeModal() {
                // Set current values in the form
                document.getElementById('card-width').value = currentCustomization.width;
                document.getElementById('card-padding').value = currentCustomization.padding;
                document.getElementById('custom-bg-color').value = currentCustomization.bgColor;
                document.getElementById('custom-text-color').value = currentCustomization.textColor;
                document.getElementById('title-size').value = currentCustomization.titleSize;
                document.getElementById('artist-size').value = currentCustomization.artistSize;
                document.getElementById('details-size').value = currentCustomization.detailsSize;
                document.getElementById('tracks-size').value = currentCustomization.tracksSize;
                
                // Select the correct color options
                document.querySelectorAll('#bg-color-options .color-option').forEach(option => {
                    if (option.getAttribute('data-color') === currentCustomization.bgColor) {
                        option.classList.add('selected');
                    } else {
                        option.classList.remove('selected');
                    }
                });
                
                document.querySelectorAll('#text-color-options .color-option').forEach(option => {
                    if (option.getAttribute('data-color') === currentCustomization.textColor) {
                        option.classList.add('selected');
                    } else {
                        option.classList.remove('selected');
                    }
                });
                
                // Select the correct font option
                document.querySelectorAll('#font-options .font-option').forEach(option => {
                    if (option.getAttribute('data-font') === currentCustomization.fontFamily) {
                        option.classList.add('selected');
                    } else {
                        option.classList.remove('selected');
                    }
                });
                
                // Show the modal
                customizeModal.style.display = 'flex';
            }
            
            function applyCustomization() {
                // Get values from the form
                const width = parseInt(document.getElementById('card-width').value);
                const padding = parseInt(document.getElementById('card-padding').value);
                const bgColor = document.getElementById('custom-bg-color').value;
                const textColor = document.getElementById('custom-text-color').value;
                const titleSize = parseInt(document.getElementById('title-size').value);
                const artistSize = parseInt(document.getElementById('artist-size').value);
                const detailsSize = parseInt(document.getElementById('details-size').value);
                const tracksSize = parseInt(document.getElementById('tracks-size').value);
                
                // Get selected font
                let fontFamily = 'Montserrat';
                document.querySelectorAll('#font-options .font-option').forEach(option => {
                    if (option.classList.contains('selected')) {
                        fontFamily = option.getAttribute('data-font');
                    }
                });
                
                // Check for custom font
                const customFontUrl = document.getElementById('custom-font-url').value;
                const customFontName = document.getElementById('custom-font-name').value;
                
                if (customFontUrl && customFontName) {
                    // Load custom font
                    const fontLink = document.createElement('link');
                    fontLink.href = customFontUrl;
                    fontLink.rel = 'stylesheet';
                    document.head.appendChild(fontLink);
                    
                    fontFamily = customFontName;
                }
                
                // Update current customization
                currentCustomization = {
                    width,
                    padding,
                    bgColor,
                    textColor,
                    fontFamily,
                    titleSize,
                    artistSize,
                    detailsSize,
                    tracksSize
                };
                
                // Apply to current polaroid if available
                if (currentPolaroid) {
                    const polaroid = currentPolaroid.element;
                    polaroid.style.width = `${width}px`;
                    polaroid.style.padding = `${padding}px ${padding}px ${padding * 2}px`;
                    polaroid.style.backgroundColor = bgColor;
                    polaroid.style.color = textColor;
                    polaroid.style.fontFamily = `'${fontFamily}', sans-serif`;
                    
                    polaroid.querySelector('.polaroid-title').style.fontSize = `${titleSize}px`;
                    polaroid.querySelector('.polaroid-artist').style.fontSize = `${artistSize}px`;
                    polaroid.querySelector('.polaroid-details').style.fontSize = `${detailsSize}px`;
                    polaroid.querySelector('.polaroid-tracks').style.fontSize = `${tracksSize}px`;
                }
            }
            
            function showGroupModal() {
                // Clear previous input
                document.getElementById('group-name').value = '';
                
                // Show existing groups
                const existingGroupsContainer = document.getElementById('existing-groups');
                existingGroupsContainer.innerHTML = '';
                
                if (Object.keys(groups).length > 0) {
                    const groupsList = document.createElement('div');
                    groupsList.className = 'existing-groups-list';
                    
                    Object.keys(groups).forEach(groupId => {
                        const group = groups[groupId];
                        const groupItem = document.createElement('div');
                        groupItem.className = 'existing-group-item';
                        groupItem.innerHTML = `
                            <label>
                                <input type="radio" name="existing-group" value="${groupId}">
                                ${group.name} (${group.items.length} items)
                            </label>
                        `;
                        groupsList.appendChild(groupItem);
                    });
                    
                    existingGroupsContainer.appendChild(groupsList);
                } else {
                    existingGroupsContainer.innerHTML = '<p>No existing groups. Create a new one.</p>';
                }
                
                // Show the modal
                groupModal.style.display = 'flex';
            }
            
            function addToGroup() {
                // Check if adding to existing group or creating new
                const existingGroupRadios = document.querySelectorAll('input[name="existing-group"]');
                let selectedGroupId = null;
                
                existingGroupRadios.forEach(radio => {
                    if (radio.checked) {
                        selectedGroupId = radio.value;
                    }
                });
                
                if (selectedGroupId) {
                    // Add to existing group
                    if (!groups[selectedGroupId].items) {
                        groups[selectedGroupId].items = [];
                    }
                    
                    groups[selectedGroupId].items.push({
                        track: currentPolaroid.track,
                        customization: currentCustomization
                    });
                } else {
                    // Create new group
                    const groupName = document.getElementById('group-name').value.trim();
                    
                    if (!groupName) {
                        alert('Please enter a group name');
                        return;
                    }
                    
                    const groupId = 'group_' + Date.now();
                    groups[groupId] = {
                        id: groupId,
                        name: groupName,
                        createdAt: new Date().toISOString(),
                        items: [{
                            track: currentPolaroid.track,
                            customization: currentCustomization
                        }]
                    };
                }
                
                // Save to localStorage
                localStorage.setItem('sonroids-groups', JSON.stringify(groups));
                
                // Update groups list
                renderGroups();
                
                alert('Added to group successfully!');
            }
            
            function renderGroups() {
                const groupsList = document.getElementById('groups-list');
                groupsList.innerHTML = '';
                
                if (Object.keys(groups).length === 0) {
                    groupsList.innerHTML = '<p class="no-groups">You haven\'t created any groups yet. Add polaroids to a group from the search tab.</p>';
                    return;
                }
                
                Object.keys(groups).forEach(groupId => {
                    const group = groups[groupId];
                    const groupElement = document.createElement('div');
                    groupElement.className = 'group-item';
                    groupElement.innerHTML = `
                        <div class="group-header">
                            <h3>${group.name}</h3>
                            <div class="group-actions">
                                <button class="group-btn share-group" data-group-id="${groupId}">Share</button>
                                <button class="group-btn export-group" data-group-id="${groupId}">Export</button>
                                <button class="group-btn delete-group" data-group-id="${groupId}">Delete</button>
                            </div>
                        </div>
                        <div class="group-items" id="group-items-${groupId}">
                            <!-- Group items will be rendered here -->
                        </div>
                    `;
                    
                    groupsList.appendChild(groupElement);
                    
                    // Render group items
                    const groupItemsContainer = document.getElementById(`group-items-${groupId}`);
                    
                    if (group.items && group.items.length > 0) {
                        group.items.forEach((item, index) => {
                            const itemElement = document.createElement('div');
                            itemElement.className = 'group-polaroid-item';
                            
                            const customization = item.customization || currentCustomization;
                            const track = item.track;
                            
                            // Create track list
                            const albumWords = track.album.split(' ');
                            let trackList = '';
                            
                            if (albumWords.length > 1) {
                                const firstLine = albumWords.slice(0, Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                                const secondLine = albumWords.slice(Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                                trackList = `<p>${firstLine}</p><p>${secondLine}</p>`;
                            } else {
                                trackList = `<p>${track.album.toUpperCase()}.</p>`;
                            }
                            
                            itemElement.innerHTML = `
                                <div class="polaroid" style="width: ${customization.width}px; padding: ${customization.padding}px ${customization.padding}px ${customization.padding * 2}px; background-color: ${customization.bgColor}; color: ${customization.textColor}; font-family: '${customization.fontFamily}', sans-serif;">
                                    <div class="polaroid-content">
                                        <div class="polaroid-image">
                                            <img src="${track.image}" alt="${track.name}" crossorigin="anonymous">
                                        </div>
                                        <div class="polaroid-info">
                                            <h3 class="polaroid-title" style="font-size: ${customization.titleSize}px;">${track.name.toUpperCase()}</h3>
                                            <p class="polaroid-artist" style="font-size: ${customization.artistSize}px;">${track.artist.toUpperCase()}</p>
                                            <div class="polaroid-details" style="font-size: ${customization.detailsSize}px;">
                                                <p class="polaroid-album">${track.album}</p>
                                                <p class="polaroid-year">${track.year}</p>
                                            </div>
                                            <div class="polaroid-tracks" style="font-size: ${customization.tracksSize}px;">
                                                ${trackList}
                                            </div>
                                        </div>
                                    </div>
                                    <button class="remove-from-group" data-group-id="${groupId}" data-item-index="${index}">×</button>
                                </div>
                            `;
                            
                            groupItemsContainer.appendChild(itemElement);
                        });
                    } else {
                        groupItemsContainer.innerHTML = '<p>No items in this group yet.</p>';
                    }
                });
                
                // Add event listeners to group buttons
                document.querySelectorAll('.share-group').forEach(button => {
                    button.addEventListener('click', function() {
                        const groupId = this.getAttribute('data-group-id');
                        shareGroup(groupId);
                    });
                });
                
                document.querySelectorAll('.export-group').forEach(button => {
                    button.addEventListener('click', function() {
                        const groupId = this.getAttribute('data-group-id');
                        showExportModal(groupId);
                    });
                });
                
                document.querySelectorAll('.delete-group').forEach(button => {
                    button.addEventListener('click', function() {
                        const groupId = this.getAttribute('data-group-id');
                        deleteGroup(groupId);
                    });
                });
                
                document.querySelectorAll('.remove-from-group').forEach(button => {
                    button.addEventListener('click', function() {
                        const groupId = this.getAttribute('data-group-id');
                        const itemIndex = parseInt(this.getAttribute('data-item-index'));
                        removeFromGroup(groupId, itemIndex);
                    });
                });
            }
            
            function shareGroup(groupId) {
                // Generate share link
                const shareUrl = `${window.location.origin}/group/${groupId}`;
                
                // Show share modal
                groupShareLink.value = shareUrl;
                groupShareModal.style.display = 'flex';
            }
            
            function showExportModal(groupId) {
                // Store the group ID for export
                exportModal.setAttribute('data-group-id', groupId);
                
                // Show export modal
                exportModal.style.display = 'flex';
            }
            
            function exportImages() {
                const groupId = exportModal.getAttribute('data-group-id');
                const group = groups[groupId];
                
                if (!group || !group.items || group.items.length === 0) {
                    alert('No items to export');
                    return;
                }
                
                // Create a zip file containing all images
                alert('Downloading all images in this group...');
                
                // For simplicity, we'll just trigger download for each image
                // In a real implementation, you'd use JSZip or similar to create a zip file
                group.items.forEach((item, index) => {
                    setTimeout(() => {
                        const track = item.track;
                        const customization = item.customization || currentCustomization;
                        
                        // Create a temporary polaroid element
                        const tempPolaroid = document.createElement('div');
                        tempPolaroid.className = 'polaroid';
                        tempPolaroid.style.width = `${customization.width}px`;
                        tempPolaroid.style.padding = `${customization.padding}px ${customization.padding}px ${customization.padding * 2}px`;
                        tempPolaroid.style.backgroundColor = customization.bgColor;
                        tempPolaroid.style.color = customization.textColor;
                        tempPolaroid.style.fontFamily = `'${customization.fontFamily}', sans-serif`;
                        
                        // Create track list
                        const albumWords = track.album.split(' ');
                        let trackList = '';
                        
                        if (albumWords.length > 1) {
                            const firstLine = albumWords.slice(0, Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                            const secondLine = albumWords.slice(Math.ceil(albumWords.length / 2)).join('. ').toUpperCase() + '.';
                            trackList = `<p>${firstLine}</p><p>${secondLine}</p>`;
                        } else {
                            trackList = `<p>${track.album.toUpperCase()}.</p>`;
                        }
                        
                        tempPolaroid.innerHTML = `
                            <div class="polaroid-content">
                                <div class="polaroid-image">
                                    <img src="${track.image}" alt="${track.name}" crossorigin="anonymous">
                                </div>
                                <div class="polaroid-info">
                                    <h3 class="polaroid-title" style="font-size: ${customization.titleSize}px;">${track.name.toUpperCase()}</h3>
                                    <p class="polaroid-artist" style="font-size: ${customization.artistSize}px;">${track.artist.toUpperCase()}</p>
                                    <div class="polaroid-details" style="font-size: ${customization.detailsSize}px;">
                                        <p class="polaroid-album">${track.album}</p>
                                        <p class="polaroid-year">${track.year}</p>
                                    </div>
                                    <div class="polaroid-tracks" style="font-size: ${customization.tracksSize}px;">
                                        ${trackList}
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        // Append to body temporarily
                        tempPolaroid.style.position = 'absolute';
                        tempPolaroid.style.left = '-9999px';
                        document.body.appendChild(tempPolaroid);
                        
                        // Generate image
                        html2canvas(tempPolaroid, {
                            backgroundColor: null,
                            scale: 2,
                            logging: false,
                            useCORS: true,
                            allowTaint: false
                        }).then(canvas => {
                            // Remove temp element
                            document.body.removeChild(tempPolaroid);
                            
                            // Download image
                            const link = document.createElement('a');
                            link.download = `${track.artist} - ${track.name} Sonroid.png`;
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                        }).catch(err => {
                            console.error("Error generating image:", err);
                            document.body.removeChild(tempPolaroid);
                        });
                    }, index * 500); // Stagger downloads to avoid browser issues
                });
            }
            
            function exportPdf() {
                const groupId = exportModal.getAttribute('data-group-id');
                const group = groups[groupId];
                
                if (!group || !group.items || group.items.length === 0) {
                    alert('No items to export');
                    return;
                }
                
                // Redirect to PDF generation endpoint
                window.location.href = `/export-pdf/${groupId}`;
            }
            
            function deleteGroup(groupId) {
                if (confirm('Are you sure you want to delete this group?')) {
                    delete groups[groupId];
                    localStorage.setItem('sonroids-groups', JSON.stringify(groups));
                    renderGroups();
                }
            }
            
            function removeFromGroup(groupId, itemIndex) {
                if (confirm('Remove this item from the group?')) {
                    groups[groupId].items.splice(itemIndex, 1);
                    
                    // If group is empty, delete it
                    if (groups[groupId].items.length === 0) {
                        delete groups[groupId];
                    }
                    
                    localStorage.setItem('sonroids-groups', JSON.stringify(groups));
                    renderGroups();
                }
            }
            
            function showCreateGroupModal() {
                document.getElementById('group-name').value = '';
                document.querySelectorAll('input[name="existing-group"]').forEach(radio => {
                    radio.checked = false;
                });
                groupModal.style.display = 'flex';
            }
            
            // Initialize
            renderGroups();
        });
    </script>
    
    <!-- Add html2canvas for image generation -->
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
</body>
</html>
"""

# Group view template
GROUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ group_name }} - Sonroids Group</title>
    <meta property="og:title" content="{{ group_name }} - Sonroids Group">
    <meta property="og:description" content="Check out this Sonroids group!">
    <meta property="og:type" content="website">
    <style>
        :root {
            --bg-color: #dcd7d3;
            --text-color: #2d2b2c;
            --accent-color: #2d2b2c;
            --card-color: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
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
            color: var(--text-color);
            text-decoration: none;
            border-bottom: 1px solid var(--text-color);
            transition: opacity 0.3s;
        }

        header a:hover {
            opacity: 0.7;
        }

        .group-info {
            text-align: center;
            margin-bottom: 30px;
        }

        .group-info h2 {
            font-size: 2rem;
            margin-bottom: 10px;
        }

        .group-info p {
            font-size: 1.1rem;
            opacity: 0.8;
        }

        .group-items {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        .polaroid {
            background-color: var(--card-color);
            box-shadow: 0 4px 8px var(--shadow-color);
            padding: 15px 15px 30px;
            display: inline-block;
            width: 350px;
            max-width: 100%;
            margin: 0 auto;
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
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }

        .polaroid-artist {
            font-size: 18px;
            margin-bottom: 10px;
            opacity: 0.8;
        }

        .polaroid-details {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .polaroid-album {
            max-width: 70%;
        }

        .polaroid-year {
            font-weight: 500;
        }

        .polaroid-tracks {
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            line-height: 1.4;
            opacity: 0.7;
            margin-top: 5px;
        }

        .cta-container {
            text-align: center;
            margin-top: 40px;
        }

        .cta-button {
            display: inline-block;
            padding: 12px 24px;
            background-color: var(--accent-color);
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 1.1rem;
            transition: background-color 0.3s;
        }

        .cta-button:hover {
            opacity: 0.9;
        }

        .export-options {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }

        .export-option {
            padding: 10px 15px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            text-decoration: none;
        }

        .export-option:hover {
            opacity: 0.9;
        }

        @media (max-width: 768px) {
            .group-items {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }
            
            .polaroid {
                width: 100%;
            }
            
            .export-options {
                flex-direction: column;
                align-items: center;
            }
            
            .export-option {
                width: 80%;
                text-align: center;
                margin-bottom: 10px;
            }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>Sonroids</h1>
            <p><a href="/">Create your own polaroids</a></p>
        </header>
        
        <div class="group-info">
            <h2>{{ group_name }}</h2>
            <p>A collection of {{ item_count }} Spotify polaroids</p>
        </div>
        
        <div class="group-items">
            {% for item in items %}
            <div class="polaroid" style="width: {{ item.customization.width }}px; padding: {{ item.customization.padding }}px {{ item.customization.padding }}px {{ item.customization.padding * 2 }}px; background-color: {{ item.customization.bgColor }}; color: {{ item.customization.textColor }}; font-family: '{{ item.customization.fontFamily }}', sans-serif;">
                <div class="polaroid-content">
                    <div class="polaroid-image">
                        <img src="{{ item.track.image }}" alt="{{ item.track.name }}" crossorigin="anonymous">
                    </div>
                    <div class="polaroid-info">
                        <h3 class="polaroid-title" style="font-size: {{ item.customization.titleSize }}px;">{{ item.track.name|upper }}</h3>
                        <p class="polaroid-artist" style="font-size: {{ item.customization.artistSize }}px;">{{ item.track.artist|upper }}</p>
                        <div class="polaroid-details" style="font-size: {{ item.customization.detailsSize }}px;">
                            <p class="polaroid-album">{{ item.track.album }}</p>
                            <p class="polaroid-year">{{ item.track.year }}</p>
                        </div>
                        <div class="polaroid-tracks" style="font-size: {{ item.customization.tracksSize }}px;">
                            {% for line in item.track_list %}
                            <p>{{ line }}</p>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="export-options">
            <a href="/export-images/{{ group_id }}" class="export-option">Download All Images</a>
            <a href="/export-pdf/{{ group_id }}" class="export-option">Download as PDF</a>
        </div>
        
        <div class="cta-container">
            <a href="/" class="cta-button">Create Your Own Sonroids</a>
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

def create_track_list(album_name):
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
    customization = data.get('customization', {})
    
    if not track_data or not image_data:
        return jsonify({"error": "Missing required data"}), 400
    
    # Generate a unique ID for the polaroid
    polaroid_id = str(uuid.uuid4())
    
    # Store the polaroid data
    polaroids[polaroid_id] = {
        "track_data": track_data,
        "image_data": image_data,
        "customization": customization,
        "created_at": datetime.now().isoformat()
    }
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/polaroid/{polaroid_id}"
    
    return jsonify({
        "success": True,
        "id": polaroid_id,
        "shareUrl": share_url
    })

@app.route('/save-group', methods=['POST'])
def save_group():
    data = request.json
    group_name = data.get('name')
    items = data.get('items', [])
    
    if not group_name or not items:
        return jsonify({"error": "Missing required data"}), 400
    
    # Generate a unique ID for the group
    group_id = str(uuid.uuid4())
    
    # Store the group data
    groups[group_id] = {
        "name": group_name,
        "items": items,
        "created_at": datetime.now().isoformat()
    }
    
    # Generate a shareable URL
    share_url = request.url_root.rstrip('/') + f"/group/{group_id}"
    
    return jsonify({
        "success": True,
        "id": group_id,
        "shareUrl": share_url
    })

@app.route('/polaroid/<polaroid_id>')
def view_polaroid(polaroid_id):
    if polaroid_id not in polaroids:
        return "Polaroid not found", 404
    
    polaroid = polaroids[polaroid_id]
    image_data = polaroid["image_data"]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sonroids - View Polaroid</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Montserrat', sans-serif;
                background-color: #dcd7d3;
                color: #2d2b2c;
                text-align: center;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                margin-bottom: 20px;
            }}
            .polaroid-image {{
                max-width: 100%;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            .cta {{
                margin-top: 30px;
            }}
            .cta a {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #2d2b2c;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <h1>Sonroids</h1>
            <div>
                <img src="{image_data}" alt="Spotify Polaroid" class="polaroid-image">
            </div>
            <div class="cta">
                <a href="/">Create Your Own Sonroids</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/group/<group_id>')
def view_group(group_id):
    if group_id not in groups:
        return "Group not found", 404
    
    group = groups[group_id]
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
    
    return render_template_string(
        GROUP_TEMPLATE,
        group_name=group_name,
        group_id=group_id,
        items=processed_items,
        item_count=len(items)
    )

@app.route('/export-images/<group_id>')
def export_images(group_id):
    if group_id not in groups:
        return "Group not found", 404
    
    # In a real implementation, you would generate a zip file with all images
    # For simplicity, we'll just return a message
    return """
    <html>
    <head>
        <title>Downloading Images</title>
        <script>
            alert('In a real implementation, this would download a zip file with all images. For now, please download each image individually from the group page.');
            window.location.href = '/group/""" + group_id + """';
        </script>
    </head>
    <body>
        <p>Redirecting...</p>
    </body>
    </html>
    """

@app.route('/export-pdf/<group_id>')
def export_pdf(group_id):
    if group_id not in groups:
        return "Group not found", 404
    
    group = groups[group_id]
    group_name = group["name"]
    items = group["items"]
    
    # In a real implementation, you would generate a PDF with all polaroids
    # For simplicity, we'll just return a message
    return """
    <html>
    <head>
        <title>Generating PDF</title>
        <script>
            alert('In a real implementation, this would generate and download a PDF with all polaroids. For now, please download each image individually from the group page.');
            window.location.href = '/group/""" + group_id + """';
        </script>
    </head>
    <body>
        <p>Redirecting...</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
