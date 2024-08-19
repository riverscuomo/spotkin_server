
import datetime
from spotkin.scripts.process_job import process_job
import time
import spotipy
from flask import jsonify


class JobService:
    def __init__(self, data_service, spotify_service):
        self.data_service = data_service
        self.spotify_service = spotify_service

    def process_job(self, request):
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
        all_jobs = self.data_service.get_all_data()
        now = datetime.datetime.now()
        current_hour = now.hour

        for user_id, user_data in all_jobs.items():
            job = user_data.get('job', {})
            if job.get('scheduled_time') == current_hour:
                try:
                    token_info = self.spotify_service.refresh_token_if_expired(
                        user_data['token'])
                    spotify = self.spotify_service.create_spotify_client(
                        token_info)
                    result = process_job(spotify, job)

                    # Update the stored token info and last processed time
                    user_data['token'] = token_info
                    user_data['last_processed'] = now.isoformat()
                    self.data_service.store_job_and_token(
                        user_id, job, token_info)

                    print(f"Job processed successfully for user: {user_id}")
                except Exception as e:
                    print(f"Error processing job for user {user_id}: {str(e)}")

    def get_schedule(self):
        all_jobs = self.data_service.get_all_data()
        schedule_info = {
            user_id: {
                'scheduled_time': job['scheduled_time'],
                'last_processed': job.get('last_processed', 'Never'),
            } for user_id, job in all_jobs.items()
        }
        return jsonify({"status": "success", "schedule": schedule_info})

    def update_job_schedule(self, data):
        user_id = data['user_id']
        new_time = data['new_time']

        all_jobs = self.data_service.get_all_data()
        if user_id in all_jobs:
            all_jobs[user_id]['scheduled_time'] = new_time
            self.data_service.store_job_and_token(
                user_id, all_jobs[user_id], all_jobs[user_id]['token'])
            return jsonify({"status": "updated", "new_time": new_time})
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404
