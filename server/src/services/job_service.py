import datetime
from server.src.models.models import Ingredient, Job, User
from spotkin_tools.scripts.process_job import process_job as tools_process_job
import time
import spotipy
from flask import jsonify
from server.src.models.models import db


class JobService:
    def __init__(self, data_service, spotify_service):
        self.data_service = data_service
        self.spotify_service = spotify_service

    def add_job(self, user_id, job_data):
        new_job = Job(
            user_id=user_id,
            playlist_id=job_data['playlist_id'],
            name=job_data['name'],
            scheduled_time=job_data.get('scheduled_time'),
            description=job_data.get('description'),
            ban_skits=job_data.get('ban_skits', False)
        )

        for ingredient_data in job_data.get('recipe', []):
            ingredient = Ingredient(
                playlist_id=ingredient_data['source_playlist_id'],
                playlist_name=ingredient_data['source_playlist_name'],
                quantity=ingredient_data['quantity']
            )
            new_job.ingredients.append(ingredient)

        db.session.add(new_job)
        db.session.commit()
        return new_job.to_dict()

    # Ensure the user exists before creating/updating a job
    def ensure_user_exists(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            # Create user if they don't exist (adjust as necessary for your user fields)
            new_user = User(id=user_id)  # Example
            db.session.add(new_user)
            db.session.commit()

    def update_job(self, job_id, updated_job_data, user_id):
        # Try to find the existing job by job_id and user_id
        job = Job.query.filter_by(id=job_id, user_id=user_id).first()

        if job:
            # Update only attributes that are part of the Job model
            for key, value in updated_job_data.items():
                print(key, value)
                if hasattr(job, key):
                    setattr(job, key, value)
        else:
            # Create a new job if it doesn't exist
            job = Job.from_dict(updated_job_data)
            job.id = job_id  # Assign the provided job_id
            job.user_id = user_id  # Ensure the job is linked to the correct user
            db.session.add(job)

        db.session.commit()  # Commit the changes to the database
        return job.to_dict()  # Return the job as a dictionary

    def get_jobs(self, user_id):
        jobs = Job.query.filter_by(user_id=user_id).all()
        print([job.name for job in jobs])
        return [job.to_dict() for job in jobs]

    def delete_job(self, user_id, job_index):
        self.data_service.delete_job(user_id, job_index)

    def process_job(self, job_id, request):
        if 'Authorization' not in request.headers:
            return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

        access_token = request.headers['Authorization']
        refresh_token = request.headers.get('Refresh-Token')

        if not refresh_token:
            return jsonify({'status': 'error', 'message': 'Refresh token is missing.'}), 401

        try:
            spotify = spotipy.Spotify(auth=access_token)
            user = spotify.current_user()
            user_id = user['id']

            job = Job.query.filter_by(id=job_id, user_id=user_id).first()

            if not job:
                return jsonify({'status': 'error', 'message': 'Job not found.'}), 404

            result = self._process_job_logic(spotify, job)

            return jsonify({
                "message": "Job processed successfully",
                "result": result,
            }), 200

        except spotipy.exceptions.SpotifyException as e:
            return jsonify({'status': 'error', 'message': str(e)}), 401
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

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
