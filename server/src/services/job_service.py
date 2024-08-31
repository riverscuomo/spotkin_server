import datetime
from spotkin_tools.scripts.process_job import process_job
import time
import spotipy
from flask import jsonify


class JobService:
    def __init__(self, data_service, spotify_service):
        self.data_service = data_service
        self.spotify_service = spotify_service

    def get_jobs(self, user_id):
        all_data = self.data_service.get_all_data()
        if user_id in all_data:
            return all_data[user_id].get('jobs', [])
        return []

    def add_job(self, user_id, job, token_info):
        self.data_service.store_job_and_token(user_id, job, token_info)

    def delete_job(self, user_id, job_index):
        self.data_service.delete_job(user_id, job_index)

    def process_job(self, request):
        if 'Authorization' not in request.headers:
            return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

        access_token = request.headers['Authorization'].replace('Bearer ', '')
        refresh_token = request.headers.get('Refresh-Token')

        if not refresh_token:
            return jsonify({'status': 'error', 'message': 'Refresh token is missing.'}), 401

        try:
            # First 20 characters
            print(f"Access token prefix: {access_token[:20]}...")
            spotify = spotipy.Spotify(auth=access_token)
            print(
                f"Spotify client created with token prefix: {spotify._auth[:20]}...")

            try:
                user = spotify.me()
                print(f"Successfully retrieved user: {user['id']}")
            except spotipy.SpotifyException as e:
                print(f"Spotify API error: {str(e)}")
                user = spotify.current_user()

            user_id = user['id']

            job = request.json

            # Set default values for missing properties
            default_job = {
                'name': '',
                'playlist_id': '',
                'scheduled_time': 0,
                'description': '',
                'ban_skits': False,
                'last_track_ids': [],
                'banned_artists': [],
                'banned_tracks': [],
                'banned_genres': [],
                'exceptions_to_banned_genres': [],
                'recipe': [],
                'min_popularity': None,
                'max_popularity': None,
                'min_duration': None,
                'max_duration': None,
                'min_danceability': None,
                'max_danceability': None,
                'min_energy': None,
                'max_energy': None,
                'min_acousticness': None,
                'max_acousticness': None,
            }

            # Update default_job with received values
            default_job.update(job)
            job = default_job

            # Convert integer values to doubles for Spotify API
            for key in ['min_danceability', 'max_danceability', 'min_energy', 'max_energy', 'min_acousticness', 'max_acousticness']:
                if job[key] is not None:
                    job[key] = job[key] / 100.0

            result = process_job(spotify, job)

            # Store the job and token info
            token_info = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                # Assume 1 hour validity
                'expires_at': int(time.time()) + 3600,
            }
            self.data_service.store_job_and_token(user_id, job, token_info)

            return jsonify({
                "message": "Job processed successfully",
                "result": result,
            }), 200

        except spotipy.exceptions.SpotifyException as e:
            return jsonify({'status': 'error', 'message': str(e)}), 401
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    def process_scheduled_jobs(self):
        print('process_scheduled_jobs...')
        all_jobs = self.data_service.get_all_data()
        now = datetime.datetime.now()
        current_hour = now.hour

        for user_id, user_data in all_jobs.items():
            jobs = user_data.get('jobs', [])
            for job in jobs:
                if job.get('scheduled_time') == current_hour:
                    print(
                        f"Processing job for user: {user_id} because scheduled time {job.get('scheduled_time')} matches current hour {current_hour}")
                    try:
                        token_info = self.spotify_service.refresh_token_if_expired(
                            user_data['token'])
                        spotify = self.spotify_service.create_spotify_client(
                            token_info)
                        result = process_job(spotify, job)

                        # Update the stored token info and last processed time
                        user_data['token'] = token_info
                        job['last_processed'] = now.isoformat()
                        self.data_service.store_job_and_token(
                            user_id, job, token_info)

                        print(
                            f"Job processed successfully for user: {user_id}")
                    except Exception as e:
                        print(
                            f"Error processing job for user {user_id}: {str(e)}")
                else:
                    print(
                        f"Skipping job for user: {user_id} because scheduled time does not match current hour")

    def get_schedule(self):
        all_jobs = self.data_service.get_all_data()
        schedule_info = {
            user_id: {
                'jobs': [{
                    'name': job.get('name', 'Unnamed job'),
                    'scheduled_time': job['scheduled_time'],
                    'last_processed': job.get('last_processed', 'Never'),
                } for job in user_data.get('jobs', [])]
            } for user_id, user_data in all_jobs.items()
        }
        return jsonify({"status": "success", "schedule": schedule_info})

    def update_job_schedule(self, data):
        user_id = data['user_id']
        new_time = data['new_time']
        job_name = data.get('job_name', None)

        all_jobs = self.data_service.get_all_data()
        if user_id in all_jobs:
            for job in all_jobs[user_id]['jobs']:
                if job_name is None or job['name'] == job_name:
                    job['scheduled_time'] = new_time
            self.data_service.store_job_and_token(
                user_id, all_jobs[user_id]['jobs'], all_jobs[user_id]['token'])
            return jsonify({"status": "updated", "new_time": new_time})
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404