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

def create_spotify_client(token):
    return spotipy.Spotify(auth=token)

@app.route('/process_jobs', methods=['POST'])
def process_jobs():
    print("process_jobs")

    if 'Authorization' not in request.headers:
        return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

    token = request.headers['Authorization'].replace('Bearer ', '')

    try:
        spotify = create_spotify_client(token)
        user = spotify.current_user()
        print(user)

        if request.is_json:
            jobs = request.get_json()
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
