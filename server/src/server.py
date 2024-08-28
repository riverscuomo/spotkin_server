
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from server.src.routes.routes import register_routes
from server.src.services.spotify_service import SpotifyService
from server.src.services.job_service import JobService
from server.src.services.data_service import DataService
import os
from server.database.database import init_db


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

# Use the DATABASE_URL environment variable for the connection string
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')


# Initialize the database
db_session = init_db(app)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
