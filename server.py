import datetime
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask, session
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotkin.scripts.process_job import process_job
import os
import json
import gzip
import base64
from flask import jsonify
# Load environment variables
load_dotenv()

app = Flask(__name__)
# cors
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')


def store_job(user_id, job_data):
    """ To stay within the 32KB limit:
    - Remove oldest job if limit exceeded"""
    all_jobs = get_all_jobs()
    all_jobs[user_id] = job_data
    jobs_str = json.dumps(all_jobs)
    if len(jobs_str) > 32000:  # Leave some buffer
        # Remove oldest job if limit exceeded
        oldest_user = min(
            all_jobs, key=lambda k: all_jobs[k].get('last_updated', 0))
        del all_jobs[oldest_user]
    os.environ['SPOTKIN_DATA'] = json.dumps(all_jobs)


def get_job(user_id):
    all_jobs = get_all_jobs()
    return all_jobs.get(user_id)


def get_all_jobs():
    jobs_str = os.environ.get('SPOTKIN_DATA', '{}')
    return json.loads(jobs_str)


def delete_job(user_id):
    all_jobs = get_all_jobs()
    if user_id in all_jobs:
        del all_jobs[user_id]
        os.environ['SPOTKIN_DATA'] = json.dumps(all_jobs)


def create_spotify_client(token_info):
    return spotipy.Spotify(auth=token_info['access_token'])


def get_all_data():
    print('Getting all data')
    data_str = os.environ.get('SPOTKIN_DATA', '{}')
    print(f"Data string: {data_str[:100]}...")
    return json.loads(data_str)


def store_data(data):
    data_str = json.dumps(data)
    os.environ['SPOTKIN_DATA'] = data_str
    # Print first 100 chars for debugging
    print(f"Stored data in memory: {data_str[:100]}...")

    # Update Heroku config var
    heroku_api_key = os.environ.get('HEROKU_API_KEY')
    app_name = os.environ.get('HEROKU_APP_NAME')

    if heroku_api_key and app_name:
        url = f"https://api.heroku.com/apps/{app_name}/config-vars"
        headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {heroku_api_key}",
            "Content-Type": "application/json"
        }
        payload = {"SPOTKIN_DATA": data_str}

        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Successfully updated Heroku config var")
        else:
            print(
                f"Failed to update Heroku config var. Status code: {response.status_code}")
    else:
        print(
            "HEROKU_API_KEY or HEROKU_APP_NAME not set. Unable to update Heroku config var.")


def store_job_and_token(user_id, job_data, token_info):
    print('Storing job and token')
    all_data = get_all_data()
    all_data[user_id] = {
        'job': job_data,
        'token': token_info,
        'last_updated': int(time.time())
    }
    data_str = json.dumps(all_data)
    if len(data_str) > 32000:  # Leave some buffer
        oldest_user = min(all_data, key=lambda k: all_data[k]['last_updated'])
        del all_data[oldest_user]
    store_data(all_data)
    print(f"Stored job and token for user {user_id}")


def get_job_and_token(user_id):
    all_data = get_all_data()
    return all_data.get(user_id)


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-library-read playlist-modify-public playlist-modify-private"
    )


def refresh_token_if_expired(token_info):
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


def compress_json(data):
    json_str = json.dumps(data)
    compressed = gzip.compress(json_str.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')


def decompress_json(compressed_str):
    try:
        decoded = base64.b64decode(compressed_str)
        decompressed = gzip.decompress(decoded)
        return json.loads(decompressed.decode('utf-8'))
    except Exception:
        # If decompression fails, assume it's not compressed
        return json.loads(compressed_str)


def get_all_data():
    # Retrieve data from Heroku config var
    data_str = os.environ.get('SPOTKIN_DATA', '{}')
    try:
        # First, try to parse it as regular JSON
        return json.loads(data_str)
    except json.JSONDecodeError:
        # If that fails, try to decompress it
        return decompress_json(data_str)


def store_job_and_token(user_id, job, token_info):
    all_data = get_all_data()
    all_data[user_id] = {
        'job': job,
        'token': token_info,
        'last_updated': int(time.time())
    }
    compressed = compress_json(all_data)
    # Store the compressed data in Heroku config var
    os.environ['SPOTKIN_DATA'] = compressed


def process_scheduled_jobs():
    all_jobs = get_all_data()
    now = datetime.datetime.now()
    current_slot = f"{now.hour:02d}:{now.minute:02d}"

    for user_id, job in all_jobs.items():
        if job['scheduled_time'] == current_slot:
            print(
                f"Processing job for user: {user_id} because scheduled time {job['scheduled_time']} matches {current_slot}")
            try:
                print(f"Processing job for user: {user_id}")
                token_info = refresh_token_if_expired(job['token'])
                spotify = spotipy.Spotify(auth=token_info['access_token'])
                result = process_job(spotify, job)

                # Update the stored token info and last processed time
                job['token'] = token_info
                job['last_processed'] = now.isoformat()
                store_job_and_token(user_id, job, token_info)

                print(f"Job processed successfully for user: {user_id}")
            except Exception as e:
                print(f"Error processing job for user {user_id}: {str(e)}")
        else:
            print(
                f"Skipping job for user {user_id} because scheduled time {job['scheduled_time']} doesn't match {current_slot}")


@app.route('/refresh_jobs', methods=['POST'])
def refresh_jobs():
    """
    This endpoint now manually triggers the job processing
    """
    process_scheduled_jobs()
    return jsonify({"status": "processing complete"})


@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    """
    This endpoint returns the current schedule
    """
    all_jobs = get_all_data()

    schedule_info = {
        user_id: {
            'scheduled_time': job['scheduled_time'],
            'last_processed': job.get('last_processed', 'Never')
        } for user_id, job in all_jobs.items()
    }

    return jsonify({"status": "success", "schedule": schedule_info})


@app.route('/update_job_schedule', methods=['POST'])
def update_job_schedule():
    data = request.json
    user_id = data['user_id']
    new_time = data['new_time']

    all_jobs = get_all_data()
    if user_id in all_jobs:
        all_jobs[user_id]['scheduled_time'] = new_time
        store_job_and_token(
            user_id, all_jobs[user_id], all_jobs[user_id]['token'])
        return jsonify({"status": "updated", "new_time": new_time})
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

# @app.route('/refresh_jobs', methods=['POST'])
# def refresh_jobs():
#     print("Starting job refresh process")
#     all_data = get_all_data()
#     refresh_results = {}

#     for user_id, user_data in all_data.items():
#         print(f"Refreshing job for user: {user_id}")
#         try:
#             token_info = refresh_token_if_expired(user_data['token'])
#             spotify = spotipy.Spotify(auth=token_info['access_token'])
#             result = process_job(spotify, user_data['job'])
#             refresh_results[user_id] = "Success"

#             # Update the stored token info
#             user_data['token'] = token_info
#             store_job_and_token(user_id, user_data['job'], token_info)
#         except Exception as e:
#             print(f"Error refreshing job for user {user_id}: {str(e)}")
#             refresh_results[user_id] = f"Error: {str(e)}"

#     print("Job refresh process completed")
#     return jsonify({"status": "complete", "results": refresh_results})


@app.route('/process_job', methods=['POST'])
def process_job_api():
    if 'Authorization' not in request.headers:
        return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

    access_token = request.headers['Authorization'].replace('Bearer ', '')
    refresh_token = request.headers.get('Refresh-Token')

    if not refresh_token:
        return jsonify({'status': 'error', 'message': 'Refresh token is missing.'}), 401

    try:
        spotify = spotipy.Spotify(auth=access_token)
        user = spotify.current_user()
        user_id = user['id']

        job = request.json
        result = process_job(spotify, job)

        # Store the job and token info
        token_info = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': int(time.time()) + 3600,  # Assume 1 hour validity
        }
        store_job_and_token(user_id, job, token_info)

        return jsonify({
            "message": "Job processed successfully",
            "result": result,
        }), 200

    except spotipy.exceptions.SpotifyException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def home():
    return 'Home - Go to /spotify-login to login with Spotify.'


if __name__ == '__main__':
    app.run(debug=True)


# @app.route('/refresh_jobs', methods=['POST'])
# def refresh_jobs():
#     print("Starting job refresh process")
#     all_jobs = get_all_jobs()
#     refresh_results = {}

#     for user_id, job_data in all_jobs.items():
#         print(f"Refreshing job for user: {user_id}")
#         try:
#             # Note: You'll need to handle access token refresh here
#             # This is a placeholder and won't work as is
#             spotify = create_spotify_client(
#                 {'access_token': 'placeholder_token'})
#             result = process_job(spotify, json.loads(job_data))
#             refresh_results[user_id] = "Success"
#         except Exception as e:
#             print(f"Error refreshing job for user {user_id}: {str(e)}")
#             refresh_results[user_id] = f"Error: {str(e)}"

#     print("Job refresh process completed")
#     return jsonify({"status": "complete", "results": refresh_results})


# @app.route('/process_job', methods=['POST'])
# def process_job_api():
#     print("Entering process_job_api function")

#     if 'Authorization' not in request.headers:
#         print("Authorization header is missing")
#         return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

#     access_token = request.headers['Authorization'].replace('Bearer ', '')
#     # Print first 10 chars for security
#     print(f"Access token received: {access_token[:10]}...")

#     try:
#         print("Creating Spotify client")
#         spotify = create_spotify_client({'access_token': access_token})

#         # Ensure token is valid
#         try:
#             print("Validating token by fetching current user")
#             user = spotify.current_user()
#             user_id = user['id']
#             print(f"User ID: {user_id}")
#         except spotipy.exceptions.SpotifyException as e:
#             print(f'Spotify API error: {str(e)}')
#             return jsonify({'status': 'error', 'message': 'Invalid or expired access token'}), 401

#         if request.is_json:
#             print("Received JSON request")
#             job = request.get_json()
#             print(f"Job data received: {job}")

#             # Check if job already exists
#             print(f"Checking for existing job for user {user_id}")
#             existing_job = get_job(user_id)
#             if existing_job:
#                 print(f"Existing job found: {existing_job}")
#                 # Merge new job data with existing job
#                 job = {**json.loads(existing_job), **job}
#                 print(f"Merged job data: {job}")
#             else:
#                 print("No existing job found")

#             print("Processing job")
#             result = process_job(spotify, job)
#             print(f"Job processing result: {result}")

#             # Store the updated job
#             print(f"Storing updated job for user {user_id}")
#             store_job(user_id, json.dumps(job))
#             print("Job stored successfully")

#             return jsonify({
#                 "message": "Spotkin processed successfully",
#                 "result": result,
#                 "job_stored": True,
#             }), 200
#         else:
#             print("Received non-JSON request")
#             return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

#     except Exception as e:
#         print(f'Error processing job: {str(e)}')
#         import traceback
#         print(f'Traceback: {traceback.format_exc()}')
#         return jsonify({'status': 'error', 'message': str(e)}), 500

#     finally:
#         print("Exiting process_job_api function")

# @app.route('/process_job', methods=['POST'])
# def process_job_api():
#     if 'Authorization' not in request.headers:
#         return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

#     access_token = request.headers['Authorization'].replace('Bearer ', '')

#     try:
#         spotify = create_spotify_client({'access_token': access_token})

#         # Ensure token is valid
#         try:
#             spotify.current_user()
#         except spotipy.exceptions.SpotifyException as e:
#             print(f'Spotify API error: {str(e)}')
#             return jsonify({'status': 'error', 'message': 'Invalid or expired access token'}), 401

#         if request.is_json:
#             job = request.get_json()
#             result = process_job(spotify, job)
#             return jsonify({"message": "Spotkin processed successfully", "result": result}), 200
#         else:
#             return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

#     except Exception as e:
#         print(f'Error processing job: {str(e)}')
#         return jsonify({'status': 'error', 'message': str(e)}), 500


# def refresh_token_if_needed(refresh_token):
#     auth_manager = SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=redirect_uri
#     )
#     token_info = auth_manager.refresh_access_token(refresh_token)
#     return token_info
