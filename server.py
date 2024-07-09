from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Spotkin API!"})

# Example endpoint
@app.route('/update_playlist', methods=['POST'])
def update_playlist_route():
    data = request.json
    playlist_id = data.get('playlist_id')
    # Call your existing function to update the playlist
    # response = update_playlist(playlist_id)  # Ensure this function is imported properly
    response = "Playlist updated!"  # Placeholder response
    return jsonify({"message": response})

if __name__ == '__main__':
    app.run(debug=True)
