
from flask import jsonify, request
from server.database.database import db
from sqlalchemy import text


def register_routes(app, job_service):

    @app.route('/jobs/<user_id>', methods=['GET'])
    def get_jobs(user_id):
        jobs = job_service.get_jobs(user_id)
        return jsonify(jobs), 200

    @app.route('/jobs/<user_id>', methods=['POST'])
    def add_job(user_id):
        data = request.get_json()
        job = data.get('job')
        token_info = data.get('token_info', {})

        job_service.add_job(user_id, job, token_info)
        return jsonify({"status": "success"}), 201

    @app.route('/jobs/<user_id>/<int:job_index>', methods=['DELETE'])
    def delete_job(user_id, job_index):
        job_service.delete_job(user_id, job_index)
        return jsonify({"status": "success"}), 204

    @app.route('/process_job', methods=['POST'])
    def process_job_api():
        return job_service.process_job(request)

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
        return 'Home - Go to /spotify-login to login with Spotify.'
