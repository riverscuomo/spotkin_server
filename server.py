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
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

def create_spotify_client(token_info):
    return spotipy.Spotify(auth=token_info['access_token'])

def refresh_token_if_needed(refresh_token):
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri
    )
    token_info = auth_manager.refresh_access_token(refresh_token)
    return token_info['access_token'], token_info

@app.route('/process_jobs', methods=['POST'])
def process_jobs():
    print("process_jobs")

    if 'Authorization' not in request.headers or 'Refresh-Token' not in request.headers:
        return jsonify({'status': 'error', 'message': 'Authorization or Refresh-Token header is missing.'}), 401

    access_token = request.headers['Authorization'].replace('Bearer ', '')
    refresh_token = request.headers['Refresh-Token']

    try:
        spotify = create_spotify_client({'access_token': access_token})

        # Ensure token is valid by making any Spotify API call like getting the current user profile.
        try:
            spotify.current_user()
        except spotipy.exceptions.SpotifyException:
            print('Access token expired. Refreshing...')
            access_token, token_info = refresh_token_if_needed(refresh_token)
            spotify = create_spotify_client(token_info)

        if request.is_json:
            jobs = request.get_json()
            for job in jobs:
                process_job(spotify, job)

            return jsonify({"message": "Jobs processed", "job_count": len(jobs), "new_access_token": access_token}), 200
        else:
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'Error processing jobs', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

