from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from spotkin.scripts.api import get_spotify_client
from spotkin.scripts.process_job import process_job

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Spotkin API!"})

@app.route('/process_jobs', methods=['POST'])
def process_jobs():
    print("process_jobs")
    if request.is_json:
        jobs = request.get_json()

        spotify = get_spotify_client()

        for job in jobs:
            process_job(spotify, job)


        return jsonify({"message": "Jobs processed", "job_count": len(jobs)}), 200
    else:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    # return jsonify({"message": "test!"})




if __name__ == '__main__':
    app.run(debug=True)
