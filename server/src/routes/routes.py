from flask import json, jsonify, request, redirect
from server.database.database import db
from sqlalchemy import text
from server.src.models.models import Job, Token, User
from server.src.services.spotify_service import SpotifyService
from server.src.services.job_service import JobService
import os
import jwt

def register_routes(app, job_service):
    spotify_service = SpotifyService(
        client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.environ.get('SPOTIFY_REDIRECT_URI')
    )


    @app.route('/refresh_token', methods=['POST'])
    def refresh_token():
        access_token = request.json.get('access_token')
        if not access_token:
            return jsonify({"error": "Access token missing"}), 400

        # Assuming you have a service method to refresh tokens
        refreshed_token_info = spotify_service.refresh_token_if_expired({"access_token": access_token})
        
        if not refreshed_token_info:
            return jsonify({"error": "Token refresh failed"}), 500

        # Only send the new access token to the client
        return jsonify({"access_token": refreshed_token_info['access_token']})

    @app.route('/process_job/<int:job_id>', methods=['POST'])
    def process_job(job_id):
        # Get the job
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        # Get the access token from the request
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization token missing"}), 401

        # Extract token from the Authorization header
        access_token = auth_header.split(" ")[1]

        # Optionally, store the token in the database or use it directly
        token_info = {'access_token': access_token}

        # Create Spotify client with the provided access token
        spotify_client = spotify_service.create_spotify_client(token_info)

        # Use spotify_client in your job processing logic
        return job_service.process_job(job_id, request)


    @app.route('/jobs/<user_id>', methods=['GET'])
    def get_jobs(user_id):
        access_token = request.headers.get('Authorization')
        if not access_token:
            return jsonify({"error": "Access token missing"}), 401

        # Call get_jobs with just user_id (access_token is not needed here)
        jobs = job_service.get_jobs(user_id)
        return jsonify(jobs), 200

    @app.route('/jobs/<user_id>', methods=['POST'])
    def add_job(user_id):
        data = request.get_json()
        job = data.get('job')
        access_token = request.headers.get('Authorization')

        if not job or not access_token:
            return jsonify({"error": "Job data or access token missing"}), 400

        # Add the job using the user's access token
        job_service.add_job(user_id, job)
        return jsonify({"status": "success"}), 201

    @app.route('/jobs/<user_id>/<int:job_index>', methods=['DELETE'])
    def delete_job(user_id, job_index):
        access_token = request.headers.get('Authorization')
        if not access_token:
            return jsonify({"error": "Access token missing"}), 401

        job_service.delete_job(user_id, job_index)
        return jsonify({"status": "success"}), 204
    

    @app.route('/jobs/<job_id>', methods=['PUT'])
    def update_job(job_id):
        access_token = request.headers.get('Authorization')
        if not access_token:
            return jsonify({"error": "Access token missing"}), 401

        # Extract user_id from Spotify API using the access token
        user_id = get_user_id_from_spotify(access_token)
        

        updated_job_data = request.get_json()
        if not updated_job_data:
            return jsonify({"error": "No job data provided"}), 400

        # Call the job service to update the job with the user_id
        updated_job = job_service.update_job(job_id, updated_job_data, user_id=user_id)

        if updated_job:
            return jsonify(updated_job), 200
        else:
            return jsonify({"error": "Job not found or not updated"}), 404






    @app.route('/refresh_jobs', methods=['POST'])
    def refresh_jobs():
        job_service.process_scheduled_jobs()
        return jsonify({"status": "processing complete"})

    @app.route('/get_schedule', methods=['GET'])
    def get_schedule():
        return job_service.get_schedule()

    @app.route('/update_job_schedule', methods=['POST'])
    def update_job_schedule():
        return job_service.update_job_schedule(request.json)

    @app.route('/test_db')
    def test_db():
        try:
            result = db.session.execute(text("SELECT 1 as test")).fetchone()
            return f'Database connection successful! Test value: {result.test}'
        except Exception as e:
            return f'Database connection failed: {str(e)}'

    @app.route('/')
    def home():
        return 'Spotkin API is running!'
    


import requests

def get_user_id_from_spotify(access_token):
    url = 'https://api.spotify.com/v1/me'
    headers = {
        'Authorization': f'{access_token}'
    }

    response = requests.get(url, headers=headers)
    print(response)

    if response.status_code == 200:
        user_data = response.json()
        return user_data.get('id')  # Spotify user_id
    else:
        print(f"Failed to get user info: {response.status_code}, {response.text}")
        return None
        # return 'rcuomo'

def ensure_user_exists(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        # Create user if they don't exist
        new_user = User(id=user_id, username='Rivers Cuomo')  # Adjust fields as necessary
        db.session.add(new_user)
        db.session.commit()
    
    # @app.route('/spotify-login')
    # def spotify_login():
    #     auth_url = spotify_service.get_auth_url()
    #     print('Redirecting to:', auth_url)
    #     return redirect(auth_url)


    # @app.route('/callback')
    # def spotify_callback():
    #     code = request.args.get('code')
    #     error = request.args.get('error')

    #     if error:
    #         return f'Error: {error}', 400

    #     token_info = spotify_service.exchange_code_for_token(code)
        
    #     # Get or create user (you might want to use a real user ID here)
    #     user_id = token_info.get('user_id', 'default_user_id')  # Replace with actual user ID logic
    #     user = User.query.get(user_id)
    #     if not user:
    #         user = User(id=user_id)
    #         db.session.add(user)

    #     # Update or create token
    #     token = Token.query.get(user_id)
    #     if token:
    #         token.token_info = json.dumps(token_info)
    #     else:
    #         token = Token(user_id=user_id, token_info=json.dumps(token_info))
    #         db.session.add(token)

    #     db.session.commit()
    
    #     # Only send the access token to the client
    #     access_token = token_info['access_token']

    #     url = f"{os.environ.get('FRONTEND_URL')}/?access_token={access_token}&user_id={user_id}"

    #     print('Redirecting to:', url)
        
    #     # Redirect to the frontend with just the access token
    #     return redirect(url)


    # def get_user_token_info(user_id):
    #     token = Token.query.get(user_id)
    #     if token:
    #         return json.loads(token.token_info)
    #     return None