## .\database.py

```py
# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    # If you need to use the engine directly
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine))

    return db_session

```

## .\data_service.py

```py
import os
import json
import gzip
import base64
import time
import requests


class DataService:
    def get_all_data(self):
        print('Getting all data...')
        data_str = os.environ.get('SPOTKIN_DATA', '{}')
        if not data_str or data_str == '{}':
            print("No data found in SPOTKIN_DATA, returning empty dictionary.")
            return {}
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return self._decompress_json(data_str)

    def store_job_and_token(self, user_id, job, token_info):
        print('Storing job and token')
        all_data = self.get_all_data()
        self.print_all_jobs(all_data)

        if user_id not in all_data:
            all_data[user_id] = {'jobs': [], 'token': token_info,
                                 'last_updated': int(time.time())}

        # Check if the job already exists based on playlist_id
        job_exists = False
        for existing_job in all_data[user_id]['jobs']:
            if existing_job['playlist_id'] == job['playlist_id']:
                # Update existing job
                existing_job.update(job)
                job_exists = True
                break

        if not job_exists:
            # Add new job if it doesn't exist
            all_data[user_id]['jobs'].append(job)

        all_data[user_id]['last_updated'] = int(time.time())
        all_data[user_id]['token'] = token_info

        compressed = self._compress_json(all_data)
        os.environ['SPOTKIN_DATA'] = compressed
        self._update_heroku_config(compressed)

    def print_all_jobs(self, all_data):
        print('\nAll data:')
        i = 1
        for user, value in all_data.items():
            jobs = value.get('jobs', [])
            for job_entry in jobs:
                scheduled_time = job_entry.get('scheduled_time')
                playlist_id = job_entry.get('playlist_id')
                name = job_entry.get('name')
                index = job_entry.get('index')
                print(
                    f'{i}. {user} "{name}", Scheduled Time: {scheduled_time}, Index: {index}, Playlist ID: {playlist_id}')
                i += 1

    def delete_job(self, user_id, job_index=None):
        all_data = self.get_all_data()
        if user_id in all_data:
            if job_index is not None:
                jobs = all_data[user_id].get('jobs', [])
                if 0 <= job_index < len(jobs):
                    del jobs[job_index]
                    all_data[user_id]['jobs'] = jobs
            else:
                del all_data[user_id]
            os.environ['SPOTKIN_DATA'] = self._compress_json(all_data)

    def _compress_json(self, data):
        json_str = json.dumps(data)
        compressed = gzip.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')

    def _decompress_json(self, compressed_str):
        try:
            decoded = base64.b64decode(compressed_str)
            decompressed = gzip.decompress(decoded)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            print(f"Error decompressing JSON: {str(e)}, returning as is")
            return json.loads(compressed_str)

    def _update_heroku_config(self, compressed_data):
        heroku_api_key = os.environ.get('HEROKU_API_KEY')
        app_name = os.environ.get('HEROKU_APP_NAME')
        if heroku_api_key and app_name:
            url = f"https://api.heroku.com/apps/{app_name}/config-vars"
            headers = {
                "Accept": "application/vnd.heroku+json; version=3",
                "Authorization": f"Bearer {heroku_api_key}",
                "Content-Type": "application/json",
            }
            payload = {"SPOTKIN_DATA": compressed_data}
            response = requests.patch(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Successfully updated Heroku config var")
            else:
                print(
                    f"Failed to update Heroku config var. Status code: {response.status_code}")

```

## .\job_service.py

```py
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

```

## .\Procfile

```
web: gunicorn server:app
```

## .\pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "spotkin"
version = "0.1.0"
description = "Your package description"
```

## .\README.md

```md
# Spotkin [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)

Note: I renamed the project from "Spotnik".

A python package that updates one or more of your Spotify playlists every day with a random selection of tracks from any public playlists.

For example, I have a playlist called ["Rivers Radio"](https://open.spotify.com/playlist/1HaQfSGjNzIsiC5qOsCUcW?si=861bc59c458b4b0a) that is updated by spotkin every day.

I developed this script because I didn't like fiddling with the Spotify app all the time. I just wanted a great selection of music in one playlist every day. I've been using it every day for a few years. It's run automatically at 2am by a Windows Task Scheduler job. It works best when you draw from many playlists, especially:

- dynamic playlists like "New Music Friday" or "Today's Top Hits" because they frequently change
- large curated playlists like Rolling Stone's "fivehundredalbums"
- a playlist generated by my new_albums script which has the latest album releases in all the genres you're interested in  

You can also ban artists, tracks, or genres. That's great for avoiding music you don't like (obviously) but also for avoiding music you don't want to hear right now even though you love it. For example, I love the Beach Boys. Spotify knows that so they keep adding them to the algorthmic playlists. But I've heard all their songs a zillion times and I don't need to hear them now.

On tour, I realized I needed a second playlist, for warming up before a show, so I added the ability to update as many playlists as you want--and to set minimun values for 'energy', etc. I recommend sticking with one or two playlists, though, otherwise you're just fiddling with the Spotify app all over again.

I find that I tweak my recipe about once a week.

## This package can be used in two ways

1. As a standalone script that runs on your machine
2. As a server that can process jobs on behalf of clients. (Currently in development at spotkin_flutter). Hit the endpoint with a POST request containing the jobs and a spotify token. The server will update the playlists and return the results. The server is built with Flask and is hosted on Heroku.

## Installation

Before you can run the spotkin script, there are some pre-requisites the script assumes.

### Spotify Developer Account

The script will need a Spotify **Client Id** and **Client Secret** to interact with Spotify's Web API.

Register for a [developer account](https://developer.spotify.com) on Spotify. After registering, create a new app. Once you create a new app, a Client Id and Client Secret will be generated. You will need these in later steps.

Additionally, the spotkin script uses an Authorization Code Flow. Due to this, you will need to set a redirect URL for your app. To add a redirect URL, open the app's settings. Note: The spotkin script is only intended to run locally, on your machine, so add a redirect link to `http://localhost:8080`.

### Spotify Playlist Id

The script will need the unique ID for at least one of your Spotify playlists. This is where your spotkin playlist will be updated. To get the ID for a playlist, in Spotify, right-click on the playlist > Share > Copy Share Link. The link will contain the playlist ID. It is the string between `playlist/` and `?si=`.

### Environment Variables

You can specify custom variables to include using a `.env` file.  Alternatively, you can set them as Environment Variables.

```
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx
SPOTIFY_REDIRECT_URI=http://localhost:8080

FLASK_APP=server.py
FLASK_ENV=development
```

### Setup your settings in Google Sheets

### Import with our script

Tiny script to copy the template sheet to a user-specified gmail.
The function can be imported:

python3 copy_sheet.py "/path/to/credentials.json" "<myemail@gmail.com>"
TLDR: fetches the template sheet, duplicates it and shares the duplicated sheet to a gmail.

### Manually make a copy

<https://docs.google.com/spreadsheets/d/1z5MejG6EKg8rf8vYKeFhw9XT_3PxkDFOrPSEKT_jYqI/edit#gid=1936655481>

The spreadsheet should be called "Spotify Controller" and have a sheet named "recipes" and a sheet "settings"

Put your target playlist id(s) in the `playlist_id` row of the settings sheet.

Share your google spreadsheet with the client_email address in your google credentials file.

Set the following environment variables to get the data from the sheet:

GSPREADER_GOOGLE_CLIENT_EMAIL=client_email_from_your_creds.json
GSPREADER_GOOGLE_CREDS_PATH=path_to_your_creds.json

### To add more target playlists

Simply add columns in the "recipes" sheet and in the "settings" sheet. I like keeping it to one or two.

## Running

Once you have completed all the installation steps, run spotkin script by running `py -m spotkin`.
Run the server with 'flask run"

## Contributing

Feel free to make pull requests for any changes you'd like to see.  

see [discussions](https://github.com/riverscuomo/spotkin/discussions/11) for some ideas.

```

## .\refresh_jobs.py

```py
import requests
import os
from rich import print


def refresh_all_jobs():
    """ To be run as a scheduled job by Heroku scheduler to refresh all jobs """
    print("Running refresh_jobs.py To be run as a scheduled job by Heroku scheduler to refresh all jobs")
    app_url = os.environ.get(
        'APP_URL', 'https://spotkin-1b998975756a.herokuapp.com')
    response = requests.post(f'{app_url}/refresh_jobs')

    if response.status_code == 200:
        print("Jobs refreshed successfully")
        print(response.json())
    else:
        print(f"Error refreshing jobs: Status {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    refresh_all_jobs()

```

## .\requirements.txt

```txt
spotipy>=2.21.0
python-decouple>=3.6
python-dateutil>=2.8.2
python-dotenv>=0.21.0
rich>=12.6.0
gspreader>=0.1.20
gspread>=5.7.2
Flask>=3.0.3
Flask-Cors>=4.0.1
gunicorn>=22.0.0
requests>=2.26.0


Flask-SQLAlchemy==3.1.1
psycopg2==2.9.9
```

## .\routes.py

```py

from flask import jsonify, request
from database import db
from sqlalchemy import text


def register_routes(app, job_service):
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

```

## .\server.py

```py

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from routes import register_routes
from spotify_service import SpotifyService
from job_service import JobService
from data_service import DataService
import os
from database import init_db


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

```

## .\spotify_service.py

```py

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyService:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def create_spotify_oauth(self):
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="user-library-read playlist-modify-public playlist-modify-private",
        )

    def refresh_token_if_expired(self, token_info):
        sp_oauth = self.create_spotify_oauth()
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(
                token_info['refresh_token'])
        return token_info

    def create_spotify_client(self, token_info):
        return spotipy.Spotify(auth=token_info['access_token'])

```

## .\spotkin\build_artist_genres.py

```py
try:
    from scripts.api import get_artists_genres
except:
    from spotkin.scripts.api import get_artists_genres


def build_artist_genres(spotify, tracks):
    # list of artist ids to you can get the genre objects in one call
    artists = [track["artists"][0] for track in tracks]
    artist_ids = [artist["id"] for artist in artists]
    artist_ids = list(set(artist_ids))
    return get_artists_genres(spotify, artist_ids)

```

## .\spotkin\__init__.py

```py

```

## .\spotkin\__main__.py

```py
from datetime import datetime
from re import X
from time import sleep

try:
    from scripts.process_job import process_job
    from scripts.bans import *
    from scripts.post_description import *
    from scripts.api import *
    from scripts.utils import *
except:
    from spotkin.scripts.process_job import process_job
    from spotkin.scripts.bans import *
    from spotkin.scripts.post_description import *
    from spotkin.scripts.api import *
    from spotkin.scripts.utils import *
from dotenv import load_dotenv
import gspreader
import gspread
from rich import print

load_dotenv()

log("spotkin.setup main...")


def get_jobs_with_their_settings():
    """
    Retrieves job settings from a Google Spreadsheet named "Spotify Controller" and the sheet "settings".

    The function reads all records from the sheet and transforms them into a list of dictionaries, where each dictionary represents a job.
    Each job is a dictionary with the job name as the key and the job settings as the values.

    The settings are processed as follows:
    - If a setting contains "||", it is split into a list of items.
    - If a setting is "TRUE" or "FALSE", it is converted to a boolean value.
    - Otherwise, the setting is stripped of leading and trailing whitespace.

    For certain settings that are guaranteed to be lists (specified in `list_types`), if the setting is not already a list, it is converted into a list.

    Returns:
        jobs (list of dict): A list of dictionaries, where each dictionary represents a job with its settings.
    """

    log("gettings jobs...")

    settings_sheet = gspreader.get_sheet("Spotify Controller", "settings")
    log(f'got sheet:{str(settings_sheet)}')

    x = 0
    while x < 10:
        try:
            data = settings_sheet.get_all_records()
            break
        except gspread.exceptions.APIError as e:
            log(f'Error getting sheet data: {e}')
            x += 1
            sleep(10)

    jobs = [{"name": x} for x in list(data[0].keys())[1:]]
    settings = [x["setting"] for x in data]

    print(settings)

    for job in jobs:

        for row in data:

            item = row[job["name"]]

            if "||" in item:
                items = item.split("||")
                items = [x.strip() for x in items if x.strip() != ""]
                job[row["setting"]] = items

            elif item in ["TRUE", "FALSE"]:
                item = item == "TRUE"
                job[row["setting"]] = item

            else:
                job[row["setting"]] = item.strip()

            """ This is ugly but I needed a quick fix for the fact that we need some of the setting guaranteed to be lists """

            list_types = ['last_track_ids',
                          'banned_artist_names',
                          'banned_song_titles',
                          'banned_track_ids',
                          'banned_genres',
                          'exceptions_to_banned_genres',]

            if row["setting"] in list_types:
                if type(job[row["setting"]]) != list:
                    if job[row["setting"]] == "":
                        job[row["setting"]] = []
                    else:
                        job[row["setting"]] = [job[row["setting"]]]

    return jobs


def get_recipes_for_each_job(jobs: list):
    """
    Retrieves recipe data from a Google Spreadsheet named "Spotify Controller" and the sheet "recipes".

    The function reads all records from the sheet and transforms them into a list of dictionaries, where each dictionary represents a recipe.
    Each recipe is a dictionary with the source playlist name, source playlist id, and quantity as the keys and the corresponding values from the sheet as the values.

    The function then iterates over the list of jobs. For each job, it creates a new list of recipes where the quantity is not zero and adds this list to the job dictionary under the key "recipe".

    Args:
        jobs (list): A list of job dictionaries.

    Returns:
        jobs (list): The input list of job dictionaries, but with each job now including a "recipe" key with a list of recipe dictionaries.
    """
    recipe_sheet = gspreader.get_sheet("Spotify Controller", "recipes")
    recipe_data = recipe_sheet.get_all_records(head=1)

    for job in jobs:
        job["recipe"] = []
        for row in recipe_data:
            if row[job["name"]] != 0:
                job["recipe"].append({
                    "source_playlist_name": row["source_playlist_name"],
                    "source_playlist_id": row["source_playlist_id"],
                    "quantity": row[job["name"]],
                })
    print(jobs)
    return jobs


def main():

    log("spotkin.setup main...")
    log(str(datetime.now()))

    # spotify = get_spotify()
    spotify = get_spotify_client()

    # jobs = import_jobs()
    # log(jobs[0])

    # data = get_data()

    jobs = get_jobs_with_their_settings()

    jobs = get_recipes_for_each_job(jobs)

    # log(jobs)

    for job in jobs:

        process_job(spotify, job)

    return "Success!"


if __name__ == "__main__":

    main()


# JOBS_FILE_PATH = os.getenv("JOBS_FILE_PATH")
# ADD_LIST_FILE_PATH = os.getenv("ADD_LIST_FILE_PATH")


# def get_data():
#     log("getting the user's add list from csv file...")
#     with open(ADD_LIST_FILE_PATH) as csvfile:
#         reader = csv.DictReader(csvfile)
#         data = list(reader)
#     return data


# def import_jobs():

#     log("importing jobs from file...")

#     try:
#         return import_module(f"{JOBS_FILE_PATH}", package="spotkin").jobs
#     except ValueError as e:
#         log(f"Error importing from fiat file: {JOBS_FILE_PATH} - {e}")

```

## .\spotkin\scripts\api.py

```py
import os
import random
import spotipy
from spotipy import SpotifyOAuth, Spotify
try:
    from scripts.utils import *
except:
    from spotkin.scripts.utils import *
from dotenv import load_dotenv

load_dotenv()

# SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
# SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
# SPOTIPY_REDIRECT_URL = "http://localhost:8080"
# scope = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played,user-top-read"
# SPOTIPY_USER = os.getenv("SPOTIPY_USER")


def get_spotify_client(refresh_token: str = None, timeout: int = 20) -> Spotify:
    log("[get_spotify] Creating Spotify client")
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URL = os.getenv("SPOTIFY_REDIRECT_URL")
    SPOTIFY_SCOPE = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played"

    print(SPOTIPY_REDIRECT_URL)
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URL,
        scope=SPOTIFY_SCOPE,
        cache_path=".cache-file"  # Optional: where to store the token info
    )

    client = spotipy.Spotify(auth_manager=auth_manager)

    print(client.current_user())

    return client


def get_spotify(timeout=20) -> spotipy.Spotify:
    log("[get_spotify] Creating Spotify client")
    print(SPOTIPY_REDIRECT_URL)

    # This code currently uses the deprecated username parameter.
    token = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URL,
        scope=scope,
        username=SPOTIPY_USER,
        requests_timeout=timeout,
    )

    spotify = spotipy.Spotify(auth_manager=token, requests_timeout=timeout)
    return spotify


def sample_playlist_tracks(spotify: spotipy.Spotify, playlist_id, limit, name):
    log(
        f"- sampling up to {limit} Spotify tracks from the playlist '{name}'... "
    )
    all_tracks = get_playlist_tracks(spotify, playlist_id)
    # remove tracks with None type ids
    all_tracks = [track for track in all_tracks if track["track"]
                  is not None and track["track"]["id"] is not None]
    return random.sample(all_tracks, min(limit, len(all_tracks)))


def get_playlist_tracks(spotify: spotipy.Spotify, playlist_id):
    """
    Returns all tracks in a given playlist.
    """
    results = spotify.playlist_tracks(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])
    return tracks


def get_artists_genres(spotify: spotipy.Spotify, artist_ids):
    log("- returning artist genres for artist ids...")
    chunks = divide_chunks(artist_ids, 50)
    artist_genres = []
    for chunk in chunks:
        result = spotify.artists(chunk)["artists"]
        for item in result:
            artist_id = item["id"]
            genres = item["genres"]
            artist_genre_object = {"artist_id": artist_id, "genres": genres}
            artist_genres.append(artist_genre_object)
    return artist_genres


def get_audio_features(spotify: spotipy.Spotify, track_ids):
    """
    Retrieves audio features for a list of track IDs from the Spotify API.

    Args:
        spotify: An instance of the `spotipy.Spotify` class representing the Spotify API client.
        track_ids: A list of track IDs for which to retrieve audio features.

    Returns:
        A dictionary mapping each track ID to its corresponding audio features, excluding any features that are None.

    Examples:
        spotify = spotipy.Spotify()
        track_ids = ["track1", "track2", "track3"]
        features = get_audio_features(spotify, track_ids)
        # Returns: {"track1": {"id": "track1", "feature": "data"}, "track2": {"id": "track2", "feature": "data"}, "track3": {"id": "track3", "feature": "data"}}
    """
    log("- returning get_audio_features track ids...")
    chunks = divide_chunks(track_ids, 100)
    audio_features = []
    for chunk in chunks:
        result = spotify.audio_features(chunk)
        audio_features.extend(iter(result))
    return {v["id"]: v for v in audio_features if v is not None}


def get_playlist_track_ids(spotify: spotipy.Spotify, playlist_id, limit, skip_recents=None, name=""):
    tracks = get_playlist_tracks(spotify, playlist_id, limit, name)
    return [x["track"]["id"] for x in tracks if x["track"] is not None]

```

## .\spotkin\scripts\bans.py

```py
try:
    from scripts.utils import *
except:
    from spotkin.scripts.utils import *


class PlaylistFilter:
    """Determines whether songs belong in the playlist or not based on a job."""

    def __init__(self, job, audio_features) -> None:
        self.job = job
        self.audio_features = audio_features

    def is_banned(self, artist_genre, artist_name, track_name, track_id, track):
        return self._is_banned_by_genre(artist_genre, artist_name, track_name) or \
            self._is_banned_by_track_id(track_id, artist_name, track_name) or \
            self._is_banned_by_artist_name(artist_name, track_name) or \
            self._is_banned_by_song_title(artist_name, track_name) or \
            self._is_banned_by_low_energy(track_name, artist_name, track)

    def _is_banned_by_artist_name(self, artist_name, track_name):

        if "banned_artist_names" not in self.job:
            return False

        banned_artist_names_lowercase = [
            str(x.lower()) for x in self.job["banned_artist_names"]]

        if artist_name.lower() in banned_artist_names_lowercase:
            log(
                f"Removed {track_name} by {artist_name} because {artist_name} is in this playlist's banned artist names"
            )
            return True
        return False

    def _is_banned_by_genre(self, artist_genre, artist_name, track_name):

        if "banned_genres" not in self.job or artist_genre is None:
            return False

        # want to try being more aggressive here.
        # Now a banned genre 'rap' will reject 'Cali rap', 'trap' and 'rap metal' etc.
        elif (
            # if any of the banned genres are in the artist's genre
            any(
                banned_genre in artist_genre for banned_genre in self.job["banned_genres"])
            and artist_name not in self.job["exceptions_to_banned_genres"]
        ):
            log(
                f"Removed {track_name} by {artist_name} because genre {artist_genre} is in this playlist's banned genres"
            )
            return True
        return False

    def _is_banned_by_low_energy(self, track_name, artist_name, track):
        """Useful for workout playlists"""

        if "remove_low_energy" not in self.job or self.job["remove_low_energy"] is False:
            return False

        try:
            audio_feature = self.audio_features[track["id"]]
        except KeyError:
            return False

        loudness = audio_feature["loudness"]
        energy = audio_feature["energy"]
        speechiness = audio_feature["speechiness"]
        acousticness = audio_feature["acousticness"]

        if loudness < -15:
            log(f"- {track_name} by {artist_name} banned for low loudness: {loudness}")
            return True

        # danceability =  audio_feature["danceability"]

        elif energy < 0.51:
            log(f"- {track_name} by {artist_name} banned for low energy: {energy}")
            return True

        elif acousticness > 0.42:
            log(
                f"- {track_name} by {artist_name} banned for high acousticness: {acousticness}"
            )
            return True
        # instrumentalness =  audio_feature["instrumentalness"]
        # liveness =  audio_feature[{} banned for iveness"]
        # tempo_spotify =  audio_feature["tempo"]
        # log(audio_feature["id"],loudness,danceability,energy,speechiness,acousticness,instrumentalness,liveness,tempo_spotify)
        # if energy > 0.5:
        else:
            return False

    def _is_banned_by_song_title(self, artist_name, track_name):

        if "banned_song_titles" not in self.job:
            return False

        banned_song_titles_lowercase = [
            str(x.lower()) for x in self.job["banned_song_titles"]]

        if str(track_name).lower() in banned_song_titles_lowercase:
            log(
                f"Removed {track_name} by {artist_name} because {track_name} is in this playlist's banned song titles"
            )
            return True
        return False

    def _is_banned_by_track_id(self, track_id, artist_name, track_name):

        if "banned_track_ids" not in self.job:
            return False

        elif track_id in self.job["banned_track_ids"]:
            log(
                f"Removed {track_name} by {artist_name} because {track_id} is in this playlist's banned track_ids"
            )
            return True
        return False


# def get_fiat_sheet_bans(sheet):

#     # headerRange = "A1:ZZ1"

#     # banned_artist_names = getColValues(sheet, headerRange, "artist_name")
#     # # log(banned_artist_names)
#     # # sys.exit()
#     # bannedSongs = getColValues(sheet, headerRange, "title")
#     # bannedURIs = getColValues(sheet, headerRange, "uri")

#     data = sheet.get_all_records()

#     banned_artist_names = [str(row["artist_name"]).lower() for row in data]
#     bannedSongs = [str(row["title"]) for row in data]
#     bannedURIs = [row["uri"] for row in data]

#     return banned_artist_names, bannedSongs, bannedURIs


# def get_controller_sheet_bans(sheet):

#     data = sheet.get_all_records()

#     controller_sheet_banned_artist_names = [
#         str(row["artist_name"]).lower() for row in data if row["ban_artist"]
#     ]
#     controller_sheet_banned_track_ids = [
#         row["track_id"] for row in data if row["ban_track"]
#     ]
#     controller_sheet_liked_track_ids = [row["track_id"] for row in data if row["like"]]

#     return (
#         controller_sheet_banned_artist_names,
#         controller_sheet_banned_track_ids,
#         controller_sheet_liked_track_ids,
#     )

```

## .\spotkin\scripts\get_all_tracks.py

```py
try:
    from scripts.api import sample_playlist_tracks
    from scripts.utils import log
except:
    from spotkin.scripts.api import sample_playlist_tracks
    from spotkin.scripts.utils import log


from concurrent.futures import ThreadPoolExecutor, as_completed


def get_playlist_tracks_wrapper(args):
    spotify, playlist_id, quantity, playlist_name = args
    return sample_playlist_tracks(spotify, playlist_id, quantity, name=playlist_name)


def get_all_tracks(job, spotify):
    """
    This function will get the tracks from the playlists the user has specified
    using parallel processing to speed up execution.
    """
    target_playlist_name = job["name"]
    log(
        f"Getting tracks from the playlists earmarked for the {target_playlist_name} playlist...")

    my_picks = []
    tasks = []

    # Prepare tasks for parallel execution
    for row in job["recipe"]:
        quantity = int(row["quantity"]) if row["quantity"] else None
        if quantity is None or quantity == "" or quantity < 1:
            continue

        playlist_id = row["source_playlist_id"]
        playlist_name = row["source_playlist_name"]

        tasks.append((spotify, playlist_id, quantity, playlist_name))

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_playlist = {executor.submit(
            get_playlist_tracks_wrapper, task): task for task in tasks}

        for future in as_completed(future_to_playlist):
            task = future_to_playlist[future]
            try:
                new_tracks = future.result()
                my_picks.extend(new_tracks)
            except Exception as exc:
                playlist_name = task[3]
                log(f"Playlist {playlist_name} generated an exception: {exc}")

    return my_picks

# def get_all_tracks(job, spotify):
#     """
#     This function will get the tracks from the playlists the user has specified
#     """
#     target_playlist_name = job["name"]
#     log(
#         f"Getting tracks from the playlists earmarked for the {target_playlist_name} playlist..."
#     )
#     my_picks = []

#     for row in job["recipe"]:
#         quantity = int(row["quantity"])

#         if quantity is None or quantity == "" or quantity < 1:
#             continue

#         # parse the id of the playlist from whatever the user has entered in config.py
#         playlist_id = row["source_playlist_id"]

#         # for logging purposes
#         playlist_name = row["source_playlist_name"]

#         new_tracks = sample_playlist_tracks(
#             spotify,
#             playlist_id,
#             quantity,
#             name=playlist_name,
#         )

#         my_picks.extend(new_tracks)

#     return my_picks


# # Some playlist you want to repeat songs until
# # x number of songs have gone by
# skip_recents = (
#     all_time_played_songs_ids[: row["Skip Recents"]]
#     if row["Skip Recents"] != ""
#     else None
# )

```

## .\spotkin\scripts\post_description.py

```py
import random
import re
import os
try:
    from scripts.utils import *
except:
    from spotkin.scripts.utils import *


def getFact():
    # get the random fact
    # fact_path = "spotkin\\spotkin\\data\\randomfacts.txt"
    # fact_path = os.path.join("spotkin.spotkin", "data", "randomfacts.txt")
    # fact_path = "..\\data\\randomfacts.txt"
    # fact_path = spotkin.data.randomfacts.txt
    fact_path = os.path.join(os.path.dirname(
        __file__), '..', 'data', 'randomfacts.txt')
    with open(
        fact_path,
        "r+",
        encoding="utf-8",
    ) as file:
        randomFactList = file.readlines()
    fact = random.choice(randomFactList).strip()
    fact = re.sub(r"^\d{1,3}\.", "", fact)

    return fact


def post_description(spotify, job):
    """post a new playlist description"""
    log("Posting new playlist description...")
    fact = ""
    while not fact:
        fact = getFact()

    description = job["description"] + f"...{fact}..."

    log(f"Updating playlist description: {description}")

    spotify.user_playlist_change_details(
        spotify.me()["id"], job["playlist_id"], description=description
    )

```

## .\spotkin\scripts\process_job.py

```py

try:
    from build_artist_genres import build_artist_genres
    from scripts.api import get_audio_features, log, random
    from scripts.bans import PlaylistFilter, log
    from scripts.get_all_tracks import get_all_tracks
    from scripts.post_description import log, post_description, random
    from scripts.utils import log
except:
    from spotkin.build_artist_genres import build_artist_genres
    from spotkin.scripts.api import get_audio_features, log, random
    from spotkin.scripts.bans import PlaylistFilter, log
    from spotkin.scripts.get_all_tracks import get_all_tracks
    from spotkin.scripts.post_description import log, post_description, random
    from spotkin.scripts.utils import log

import random


def process_job(spotify, job):
    log(f"spotkin playlist {job}")
    # log(f"spotkin playlist 'Rivers Radio'")

    tracks = get_all_tracks(job, spotify)
    log(f"tracks: {len(tracks)}")

    updated_tracks = []

    # make list of just the track objects while also eliminating duplicates and empty tracks
    tracks = list({v["track"]["id"]: v["track"] for v in tracks}.values())

    track_ids = [x["id"] for x in tracks]
    log(track_ids)

    audio_features = get_audio_features(spotify, track_ids)
    artists_genres = build_artist_genres(spotify, tracks)
    playlist_filter = PlaylistFilter(job, audio_features)

    # Cull banned items from your list
    for track in tracks:
        track_id = track["id"]
        track_name = track["name"]
        artist_id = track["artists"][0]["id"]
        artist_name = track["artists"][0]["name"]
        artist_genre = next(
            (x['genres'] for x in artists_genres if x["artist_id"] == artist_id and "genres" in x), None
        )

        if playlist_filter.is_banned(artist_genre, artist_name, track_name, track_id, track):
            continue

        updated_tracks.append(track["id"])

    random.shuffle(updated_tracks)

    # if you've specify a track or tracks to always add at the end (for easy access, for example,
    # nature sounds or white noise)
    updated_tracks.extend(job["last_track_ids"])

    log("spotify.user_playlist_replace_tracks with an empty list")

    log(spotify.me()["id"])
    log(len(updated_tracks))
    # empty playlist
    result = spotify.user_playlist_replace_tracks(
        spotify.me()["id"], job["playlist_id"], []
    )
    log(result)

    limit = 100

    # log(updated_tracks)

    log("spotify.user_playlist_add_tracks")

    for chunk in (updated_tracks[i:i+limit] for i in range(0, len(updated_tracks), limit)):
        result = spotify.user_playlist_add_tracks(
            spotify.me()["id"], job["playlist_id"], chunk
        )

        # change the playlist description to a random fact
    post_description(spotify, job)

```

## .\spotkin\scripts\utils.py

```py
# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i: i + n]


def log(message: str):
    if not isinstance(message, str):
        message = str(message)
    with open("log.txt", "a") as file:
        file.write("=============================================\n")
        file.write(message + "\n")
        print(message)

        # file.write("=============================================\n")

```

