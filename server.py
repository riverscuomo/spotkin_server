from datetime import time
from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
# from spotkin.scripts.api import get_spotify_client_for_api
from spotkin.scripts.process_job import process_job
import os
from flask import Flask, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')


# Determine the redirect URI from environment variables
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

@app.route('/')
def home():
    return 'Home - Go to /spotify-login to login with Spotify.'

@app.route('/spotify-login')
def spotify_login():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
    )
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
    )
    code = request.args.get('code')
    token_info = auth_manager.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('process_jobs'))

def get_spotify_client_for_api():
    token_info = get_token()
    if not token_info:
        return None
    client = spotipy.Spotify(auth=token_info['access_token'])
    return client

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=redirect_uri,
            scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
        )
        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info

@app.route('/process_jobs', methods=['POST'])
def process_jobs():
    print("process_jobs")
    spotify = get_spotify_client_for_api()

    if not spotify:
        return redirect(url_for('spotify_login'))
    
    try:
        user = spotify.current_user()
        print(user)

        if request.is_json:
            jobs = request.get_json()

            spotify = get_spotify_client_for_api()

            for job in jobs:
                process_job(spotify, job)


            return jsonify({"message": "Jobs processed", "job_count": len(jobs)}), 200
        else:
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415


    except Exception as e:
        print(str(e))
        return jsonify({'status': 'Error processing jobs', 'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
