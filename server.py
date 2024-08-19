
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from routes import register_routes
from spotify_service import SpotifyService
from job_service import JobService
from data_service import DataService
import os

load_dotenv()


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

    # Initialize services
    data_service = DataService()
    spotify_service = SpotifyService(
        os.getenv('SPOTIFY_CLIENT_ID'),
        os.getenv('SPOTIFY_CLIENT_SECRET'),
        os.getenv('SPOTIFY_REDIRECT_URI')
    )
    job_service = JobService(data_service, spotify_service)

    # Register routes
    register_routes(app, job_service)

    return app


# Create the app instance at the module level
app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)


# import datetime
# import time
# from flask import Flask, jsonify, request
# from flask_cors import CORS
# from dotenv import load_dotenv
# import os
# from flask import Flask, session
# import requests
# import spotipy
# from spotipy.oauth2 import SpotifyOAuth
# from spotkin.scripts.process_job import process_job
# import os
# import json
# import gzip
# import base64
# from flask import jsonify
# load_dotenv()

# app = Flask(__name__)
# CORS(app)
# app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# client_id = os.getenv('SPOTIFY_CLIENT_ID')
# client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
# redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')


# def get_all_jobs():
#     jobs_str = os.environ.get('SPOTKIN_DATA', '{}')
#     return json.loads(jobs_str)


# def delete_job(user_id):
#     all_jobs = get_all_jobs()
#     if user_id in all_jobs:
#         del all_jobs[user_id]
#         os.environ['SPOTKIN_DATA'] = json.dumps(all_jobs)


# def create_spotify_client(token_info):
#     return spotipy.Spotify(auth=token_info['access_token'])


# def get_all_data():
#     print('Getting all data')
#     data_str = os.environ.get('SPOTKIN_DATA', '{}')
#     print(f"Data string: {data_str[:100]}...")
#     return json.loads(data_str)


# def get_job_and_token(user_id):
#     all_data = get_all_data()
#     return all_data.get(user_id)


# def create_spotify_oauth():
#     return SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=redirect_uri,
#         scope="user-library-read playlist-modify-public playlist-modify-private"
#     )


# def refresh_token_if_expired(token_info):
#     sp_oauth = create_spotify_oauth()
#     if sp_oauth.is_token_expired(token_info):
#         token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
#     return token_info


# def compress_json(data):
#     print('Compressing JSON')
#     json_str = json.dumps(data)
#     compressed = gzip.compress(json_str.encode('utf-8'))
#     return base64.b64encode(compressed).decode('utf-8')


# def decompress_json(compressed_str):
#     print('Decompressing JSON')
#     try:
#         decoded = base64.b64decode(compressed_str)
#         decompressed = gzip.decompress(decoded)
#         return json.loads(decompressed.decode('utf-8'))
#     except Exception as e:
#         print(f"Error decompressing JSON: {str(e)} so returning as is")
#         # If decompression fails, assume it's not compressed
#         return json.loads(compressed_str)


# def get_all_data():
#     # Retrieve data from Heroku config var
#     data_str = os.environ.get('SPOTKIN_DATA', '{}')
#     try:
#         # First, try to parse it as regular JSON
#         return json.loads(data_str)
#     except json.JSONDecodeError:
#         print('Failed to parse JSON data from config var so trying to decompress')
#         # If that fails, try to decompress it
#         return decompress_json(data_str)


# def store_job_and_token(user_id, job, token_info):
#     print('Storing job and token')
#     all_data = get_all_data()
#     all_data[user_id] = {
#         'job': job,
#         'token': token_info,
#         'last_updated': int(time.time())
#     }
#     compressed = compress_json(all_data)

#     # Store the compressed data in local environment variable
#     os.environ['SPOTKIN_DATA'] = compressed

#     # Print first 100 chars for debugging
#     print(f"Stored compressed data in memory: {compressed[:100]}...")

#     # Update Heroku config var
#     heroku_api_key = os.environ.get('HEROKU_API_KEY')
#     app_name = os.environ.get('HEROKU_APP_NAME')

#     if heroku_api_key and app_name:
#         url = f"https://api.heroku.com/apps/{app_name}/config-vars"
#         headers = {
#             "Accept": "application/vnd.heroku+json; version=3",
#             "Authorization": f"Bearer {heroku_api_key}",
#             "Content-Type": "application/json"
#         }
#         payload = {"SPOTKIN_DATA": compressed}

#         response = requests.patch(url, headers=headers, json=payload)
#         if response.status_code == 200:
#             print("Successfully updated Heroku config var")
#         else:
#             print(
#                 f"Failed to update Heroku config var. Status code: {response.status_code}")
#     else:
#         print(
#             "HEROKU_API_KEY or HEROKU_APP_NAME not set. Unable to update Heroku config var.")


# def process_scheduled_jobs():
#     all_jobs = get_all_data()
#     now = datetime.datetime.now()
#     current_hour = now.hour

#     for user_id, user_data in all_jobs.items():
#         job = user_data.get('job', {})
#         if job.get('scheduled_time') == current_hour:
#             print(
#                 f"Processing job for user: {user_id} because scheduled hour {job['scheduled_time']} matches current hour {current_hour}")
#             try:
#                 token_info = refresh_token_if_expired(user_data['token'])
#                 spotify = spotipy.Spotify(auth=token_info['access_token'])
#                 result = process_job(spotify, job)

#                 # Update the stored token info and last processed time
#                 user_data['token'] = token_info
#                 user_data['last_processed'] = now.isoformat()
#                 store_job_and_token(user_id, job, token_info)

#                 print(f"Job processed successfully for user: {user_id}")
#             except Exception as e:
#                 print(f"Error processing job for user {user_id}: {str(e)}")
#         else:
#             print(
#                 f"Skipping job for user {user_id} because scheduled hour {job.get('scheduled_time')} doesn't match current hour {current_hour}")


# @app.route('/refresh_jobs', methods=['POST'])
# def refresh_jobs():
#     """
#     This endpoint now manually triggers the job processing
#     """
#     process_scheduled_jobs()
#     return jsonify({"status": "processing complete"})


# @app.route('/get_schedule', methods=['GET'])
# def get_schedule():
#     """
#     This endpoint returns the current schedule
#     """
#     all_jobs = get_all_data()

#     schedule_info = {
#         user_id: {
#             'scheduled_time': job['scheduled_time'],
#             'last_processed': job.get('last_processed', 'Never')
#         } for user_id, job in all_jobs.items()
#     }

#     return jsonify({"status": "success", "schedule": schedule_info})


# @app.route('/update_job_schedule', methods=['POST'])
# def update_job_schedule():
#     data = request.json
#     user_id = data['user_id']
#     new_time = data['new_time']

#     all_jobs = get_all_data()
#     if user_id in all_jobs:
#         all_jobs[user_id]['scheduled_time'] = new_time
#         store_job_and_token(
#             user_id, all_jobs[user_id], all_jobs[user_id]['token'])
#         return jsonify({"status": "updated", "new_time": new_time})
#     else:
#         return jsonify({"status": "error", "message": "User not found"}), 404


# @app.route('/process_job', methods=['POST'])
# def process_job_api():
#     if 'Authorization' not in request.headers:
#         return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

#     access_token = request.headers['Authorization'].replace('Bearer ', '')
#     refresh_token = request.headers.get('Refresh-Token')

#     if not refresh_token:
#         return jsonify({'status': 'error', 'message': 'Refresh token is missing.'}), 401

#     try:
#         spotify = spotipy.Spotify(auth=access_token)
#         user = spotify.current_user()
#         user_id = user['id']

#         job = request.json

#         # Set default values for missing properties
#         default_job = {
#             'name': '',
#             'playlist_id': '',
#             'scheduled_time': 0,
#             'description': '',
#             'ban_skits': False,
#             'last_track_ids': [],
#             'banned_artists': [],
#             'banned_tracks': [],
#             'banned_genres': [],
#             'exceptions_to_banned_genres': [],
#             'recipe': [],
#             'min_popularity': None,
#             'max_popularity': None,
#             'min_duration': None,
#             'max_duration': None,
#             'min_danceability': None,
#             'max_danceability': None,
#             'min_energy': None,
#             'max_energy': None,
#             'min_acousticness': None,
#             'max_acousticness': None,
#         }

#         # Update default_job with received values
#         default_job.update(job)
#         job = default_job

#         # Convert integer values to doubles for Spotify API
#         for key in ['min_danceability', 'max_danceability', 'min_energy', 'max_energy', 'min_acousticness', 'max_acousticness']:
#             if job[key] is not None:
#                 job[key] = job[key] / 100.0

#         result = process_job(spotify, job)

#         # Store the job and token info
#         token_info = {
#             'access_token': access_token,
#             'refresh_token': refresh_token,
#             'expires_at': int(time.time()) + 3600,  # Assume 1 hour validity
#         }
#         store_job_and_token(user_id, job, token_info)

#         return jsonify({
#             "message": "Job processed successfully",
#             "result": result,
#         }), 200

#     except spotipy.exceptions.SpotifyException as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 401
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500


# @app.route('/')
# def home():
#     return 'Home - Go to /spotify-login to login with Spotify.'


# if __name__ == '__main__':
#     app.run(debug=True)
