from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotkin.scripts.process_job import process_job
import os
import json

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
    os.environ['SPOTKIN_JOBS'] = json.dumps(all_jobs)


def get_job(user_id):
    all_jobs = get_all_jobs()
    return all_jobs.get(user_id)


def get_all_jobs():
    jobs_str = os.environ.get('SPOTKIN_JOBS', '{}')
    return json.loads(jobs_str)


def delete_job(user_id):
    all_jobs = get_all_jobs()
    if user_id in all_jobs:
        del all_jobs[user_id]
        os.environ['SPOTKIN_JOBS'] = json.dumps(all_jobs)


def create_spotify_client(token_info):
    return spotipy.Spotify(auth=token_info['access_token'])


@app.route('/')
def home():
    return 'Home - Go to /spotify-login to login with Spotify.'


@app.route('/refresh_jobs', methods=['POST'])
def refresh_jobs():
    all_jobs = get_all_jobs()
    for user_id, job_data in all_jobs.items():
        # Your job refresh logic here
        pass
    return jsonify({"status": "success"})


@app.route('/process_job', methods=['POST'])
def process_job_api():
    print("Entering process_job_api function")

    if 'Authorization' not in request.headers:
        print("Authorization header is missing")
        return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

    access_token = request.headers['Authorization'].replace('Bearer ', '')
    # Print first 10 chars for security
    print(f"Access token received: {access_token[:10]}...")

    try:
        print("Creating Spotify client")
        spotify = create_spotify_client({'access_token': access_token})

        # Ensure token is valid
        try:
            print("Validating token by fetching current user")
            user = spotify.current_user()
            user_id = user['id']
            print(f"User ID: {user_id}")
        except spotipy.exceptions.SpotifyException as e:
            print(f'Spotify API error: {str(e)}')
            return jsonify({'status': 'error', 'message': 'Invalid or expired access token'}), 401

        if request.is_json:
            print("Received JSON request")
            job = request.get_json()
            print(f"Job data received: {job}")

            # Check if job already exists
            print(f"Checking for existing job for user {user_id}")
            existing_job = get_job(user_id)
            if existing_job:
                print(f"Existing job found: {existing_job}")
                # Merge new job data with existing job
                job = {**json.loads(existing_job), **job}
                print(f"Merged job data: {job}")
            else:
                print("No existing job found")

            print("Processing job")
            result = process_job(spotify, job)
            print(f"Job processing result: {result}")

            # Store the updated job
            print(f"Storing updated job for user {user_id}")
            store_job(user_id, json.dumps(job))
            print("Job stored successfully")

            return jsonify({
                "message": "Spotkin processed successfully",
                "result": result,
                "job_stored": True,
            }), 200
        else:
            print("Received non-JSON request")
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    except Exception as e:
        print(f'Error processing job: {str(e)}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        print("Exiting process_job_api function")

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


if __name__ == '__main__':
    app.run(debug=True)


# def refresh_token_if_needed(refresh_token):
#     auth_manager = SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=redirect_uri
#     )
#     token_info = auth_manager.refresh_access_token(refresh_token)
#     return token_info
