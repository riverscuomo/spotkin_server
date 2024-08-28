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

## .\dump.py

```py
from rivertils import dump

dump.dump(['.gitignore', 'dump.md', '.\spotkin\data',
           'CHANGELOG.md',  'LICENSE', '.git',])


# import os
# import fnmatch


# def load_gitignore_patterns(gitignore_path):
#     """Load .gitignore patterns into a list."""
#     patterns = []
#     if os.path.exists(gitignore_path):
#         with open(gitignore_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 # Remove comments and empty lines
#                 stripped_line = line.strip()
#                 if stripped_line and not stripped_line.startswith('#'):
#                     patterns.append(stripped_line)
#     return patterns


# def should_ignore(file_path, ignore_patterns):
#     """Check if a file should be ignored based on .gitignore patterns."""
#     for pattern in ignore_patterns:
#         if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
#             return True
#     return False


# def is_binary_file(file_path):
#     """Check if a file is binary by reading a portion of it."""
#     try:
#         with open(file_path, 'rb') as file:
#             chunk = file.read(1024)
#             if b'\0' in chunk:  # NULL byte indicates binary file
#                 return True
#     except:
#         pass
#     return False


# def traverse_project(directory, ignore_patterns):
#     """Traverse the project directory and collect file paths."""
#     files_to_include = []
#     for root, dirs, files in os.walk(directory):
#         # Check if any directories should be skipped
#         dirs[:] = [d for d in dirs if not should_ignore(
#             os.path.join(root, d), ignore_patterns)]
#         for file in files:
#             file_path = os.path.join(root, file)
#             if not should_ignore(file_path, ignore_patterns) and not is_binary_file(file_path):
#                 print(file_path)
#                 files_to_include.append(file_path)
#     return files_to_include


# def write_to_markdown(files, output_file):
#     """Write the content of files to a Markdown file."""
#     with open(output_file, 'w', encoding='utf-8') as md_file:
#         for file_path in files:
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as file:
#                     md_file.write(f"## {file_path}\n\n")
#                     md_file.write(
#                         "```" + os.path.splitext(file_path)[1].lstrip('.') + "\n")
#                     md_file.write(file.read())
#                     md_file.write("\n```\n\n")
#             except UnicodeDecodeError:
#                 print(f"Skipping {file_path} due to encoding issues.")
#             except Exception as e:
#                 print(f"An error occurred while processing {file_path}: {e}")


# def dump(additional_ignore_patterns: list[str]):
#     project_directory = '.'  # Current directory, change if needed
#     gitignore_path = os.path.join(
#         project_directory, '.gitignore', )
#     output_file = 'dump.md'

#     ignore_patterns = load_gitignore_patterns(gitignore_path)
#     ignore_patterns.append(output_file)
#     ignore_patterns.extend(additional_ignore_patterns
#                            )
#     files_to_include = traverse_project(project_directory, ignore_patterns)

#     write_to_markdown(files_to_include, output_file)
#     print(
#         f"Markdown file '{output_file}' has been created with the project content.")


# def main():
#     dump(['.gitignore', 'dump.md', '.\spotkin\data', 'CHANGELOG.md',  'LICENSE', '.git',
#          'spotkin.egg-info', '.\code-based.md', '.\dump.py', '.\.vscode', '.\spotkin\copy_sheet.py'])


# if __name__ == "__main__":
#     main()

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
   rivertils>=0.1.11
```

## .\routes.py

```py

from flask import jsonify, request


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

## .\test.txt

```txt
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
```

## .\.vscode\settings.json

```json
{
    "workbench.colorCustomizations": {
        "activityBar.activeBackground": "#268a00",
        "activityBar.background": "#268a00",
        "activityBar.foreground": "#e7e7e7",
        "activityBar.inactiveForeground": "#e7e7e799",
        "activityBarBadge.background": "#0035bf",
        "activityBarBadge.foreground": "#e7e7e7",
        "commandCenter.border": "#e7e7e799",
        "sash.hoverBorder": "#268a00",
        "statusBar.background": "#185700",
        "statusBar.foreground": "#e7e7e7",
        "statusBarItem.hoverBackground": "#268a00",
        "statusBarItem.remoteBackground": "#185700",
        "statusBarItem.remoteForeground": "#e7e7e7",
        "titleBar.activeBackground": "#185700",
        "titleBar.activeForeground": "#e7e7e7",
        "titleBar.inactiveBackground": "#18570099",
        "titleBar.inactiveForeground": "#e7e7e799",
        "tab.activeBorder": "#268a00"
    },
    "peacock.color": "#185700",
    "dotenv.enableAutocloaking": false
}
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

## .\spotkin\copy_sheet.py

```py
import argparse
import pygsheets  # pip3 install pygsheets


TEMPLATE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1z5MejG6EKg8rf8vYKeFhw9XT_3PxkDFOrPSEKT_jYqI/edit#gid=1936655481"
SHEET_TITLE = "Spotify Controller"


def copy_sheet(service_file, gmail):
	gc = pygsheets.authorize(service_file=service_file)

	template_sh = gc.open_by_url(TEMPLATE_SHEET_URL)
	copied_sh = gc.create(title=SHEET_TITLE, template=template_sh)

	# optionally remove "validation" worksheet
	val_wks = [wks for wks in copied_sh.worksheets() if wks.title == "validation"]
	if (val_wks):
	    copied_sh.del_worksheet(val_wks[0])

	copied_sh.share(gmail, role="writer")
	print('shared sheet "%s" to %s' % (SHEET_TITLE, gmail))
	return


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='copy sheet')
	parser.add_argument('service_file', type=str, help='path to auth service file')
	parser.add_argument('gmail', type=str, help='gmail to share to')
	args = parser.parse_args()

	copy_sheet(args.service_file, args.gmail)

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

## .\spotkin.egg-info\dependency_links.txt

```txt


```

## .\spotkin.egg-info\PKG-INFO

```
Metadata-Version: 2.1
Name: spotkin
Version: 0.1.0
Summary: Your package description
License-File: LICENSE

```

## .\spotkin.egg-info\SOURCES.txt

```txt
LICENSE
README.md
pyproject.toml
spotkin/__init__.py
spotkin/__main__.py
spotkin/build_artist_genres.py
spotkin/copy_sheet.py
spotkin.egg-info/PKG-INFO
spotkin.egg-info/SOURCES.txt
spotkin.egg-info/dependency_links.txt
spotkin.egg-info/top_level.txt
spotkin/data/_example_jobs.py
spotkin/scripts/api.py
spotkin/scripts/bans.py
spotkin/scripts/get_all_tracks.py
spotkin/scripts/post_description.py
spotkin/scripts/process_job.py
spotkin/scripts/utils.py
```

## .\spotkin.egg-info\top_level.txt

```txt
spotkin

```

