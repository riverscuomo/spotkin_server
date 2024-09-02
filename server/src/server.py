from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from server.src.routes.routes import register_routes
from server.src.services.spotify_service import SpotifyService
from server.src.services.job_service import JobService
from server.src.services.data_service import DataService
from server.database.database import db, init_db
import os

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

    # Set the SQLAlchemy Database URI
    db_url = os.getenv('DATABASE_URL')

    # Replace postgres:// with postgresql:// if necessary
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    print(db_url)

    # Initialize the database
    init_db(app)

    migrate = Migrate(app, db)

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

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)