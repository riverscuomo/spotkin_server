from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from server.src.routes.routes import register_routes
from server.src.services.spotify_service import SpotifyService
from server.src.services.job_service import JobService
from server.src.services.data_service import DataService
from server.src.models import db
import os
from server.database.database import init_db

# Load environment variables from .env file
load_dotenv()
# Test if environment variables are loaded correctly
print(f"FLASK_APP: {os.getenv('FLASK_APP')}")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")


from server.database.database import db, init_db

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

    # Initialize the database
    db = init_db(app)

    with app.app_context():
        db.create_all()

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

if __name__ == '__main__':
    app.run(debug=True)
