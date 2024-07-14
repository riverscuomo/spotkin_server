from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotkin.scripts import process_job as process_single_job


# Load environment variables
load_dotenv()

app = Flask(__name__)
# cors
CORS(app)
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
    return token_info


@app.route('/')
def home():
    return 'Home - Go to /spotify-login to login with Spotify.'


@app.route('/process_job', methods=['POST'])
def process_job():
    if 'Authorization' not in request.headers:
        return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

    access_token = request.headers['Authorization'].replace('Bearer ', '')

    try:
        spotify = create_spotify_client({'access_token': access_token})

        # Ensure token is valid
        try:
            spotify.current_user()
        except spotipy.exceptions.SpotifyException as e:
            print(f'Spotify API error: {str(e)}')
            return jsonify({'status': 'error', 'message': 'Invalid or expired access token'}), 401

        if request.is_json:
            job = request.get_json()
            result = process_single_job(spotify, job)
            return jsonify({"message": "Job processed successfully", "result": result}), 200
        else:
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    except Exception as e:
        print(f'Error processing job: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)


# @app.route('/spotify-login')
# def spotify_login():
#     auth_manager = SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=redirect_uri,
#         scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
#     )
#     auth_url = auth_manager.get_authorize_url()
#     return jsonify({'auth_url': auth_url})


# @app.route('/callback')
# def callback():
#     auth_manager = SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=redirect_uri,
#         scope="playlist-modify-private playlist-modify-public user-library-read playlist-read-private user-library-modify user-read-recently-played"
#     )
#     code = request.args.get('code')
#     token_info = auth_manager.get_access_token(code)
#     session['token_info'] = token_info
#     session['refresh_token'] = token_info['refresh_token']
#     return jsonify({
#         'access_token': token_info['access_token'],
#         'refresh_token': token_info['refresh_token'],
#         'expires_in': token_info['expires_in']
#     })
