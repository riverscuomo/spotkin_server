from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from spotkin.scripts.api import get_spotify_client
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

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/spotify-login')
def spotify_login():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
    )
    auth_url = auth_manager.get_authorize_url()
    session['spotify_auth_manager'] = auth_manager
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_manager = session.get('spotify_auth_manager')
    if not auth_manager:
        return redirect(url_for('spotify_login'))

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    session['spotify_token'] = auth_manager.get_access_token()
    return redirect(url_for('process_jobs'))

def get_spotify_client(refresh_token: str = None, timeout: int = 20) -> spotipy.Spotify:
    print("[get_spotify] Creating Spotify client")
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played",
        cache_path=".cache-file"
    )

    client = spotipy.Spotify(auth_manager=auth_manager)
    print(client.current_user())
    return client

@app.route('/process_jobs', methods=['POST'])
def process_jobs():
    print("process_jobs")
    if request.is_json:
        jobs = request.get_json()

        spotify = get_spotify_client()

        for job in jobs:
            process_job(spotify, job)


        return jsonify({"message": "Jobs processed", "job_count": len(jobs)}), 200
    else:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    # return jsonify({"message": "test!"})




if __name__ == '__main__':
    app.run(debug=True)
