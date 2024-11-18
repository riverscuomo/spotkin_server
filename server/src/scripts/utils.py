from datetime import datetime
import os
from server.src.models.models import Job, Token, User
from server.database.database import db
from server.src.server import create_app
from server.src.services.data_service import DataService
from server.src.services.job_service import JobService
from server.src.services.spotify_service import SpotifyService
from spotipy import SpotifyOAuth
import spotipy

katie_id = "fshkks"
rivers = "rcuomo"

katie_job_id = "5c108e63-a942-4bbe-8d73-fc822a151147"
rivers_job_id = "4295483a-734b-4203-b3c2-0e2dbfece36a"


def normalize_values():
    jobs = Job.query.all()  # Get all jobs in the database

    for job in jobs:
        # Normalize values if they are still in the 1-100 range
        if job.min_energy and job.min_energy > 0:
            job.min_energy = 1
        if job.max_energy and job.max_energy > 0:
            job.max_energy = 1

        if job.min_danceability and job.min_danceability > 0:
            job.min_danceability = 1
        if job.max_danceability and job.max_danceability > 0:
            job.max_danceability = 1

        if job.min_acousticness and job.min_acousticness > 0:
            job.min_acousticness = 1
        if job.max_acousticness and job.max_acousticness > 0:
            job.max_acousticness = 1

        if job.min_popularity and job.min_popularity > 0:
            job.min_popularity = 50

        # Commit the changes to the database
        db.session.commit()


def remove_duplicate_ingredients():
    jobs = Job.query.all()  # Get all jobs in the database

    for job in jobs:
        # Use a set to track playlist IDs and remove duplicates
        seen_playlists = set()
        ingredients_to_remove = []

        for ingredient in job.recipe:
            playlist_id = ingredient.playlist.get('id')

            if playlist_id in seen_playlists:
                # Mark the duplicate for removal
                ingredients_to_remove.append(ingredient)
            else:
                seen_playlists.add(playlist_id)

        # Remove the duplicates from the job.recipe list and the database
        for ingredient in ingredients_to_remove:
            print(
                f"Removing duplicate ingredient with playlist_id: {ingredient.playlist.get('id')}")
            job.recipe.remove(ingredient)  # Remove from the relationship list
            db.session.delete(ingredient)  # Remove from the database

    db.session.commit()  # Commit all deletions


def inspect_jobs():
    jobs = Job.query.all()  # Get all jobs in the database

    # # get current time as int
    # now = datetime.now()
    # # set created_at to 3 days ago if None
    # for job in jobs:
    #     if job.created_at is None:
    #         job.created_at = int((now - timedelta(days=3)).timestamp())
    #         db.session.commit()

    # sort the jobs by last_autorun
    jobs.sort(key=lambda x: x.last_autorun if x.last_autorun is not None else 0)

    for job in jobs:
        # convert time values to human readable
        scheduled_time = datetime.fromtimestamp(
            job.scheduled_time).strftime('%Y-%m-%d %H:%M:%S') if job.scheduled_time is not None else None

        created_at = datetime.fromtimestamp(job.created_at).strftime(
            '%Y-%m-%d %H:%M:%S') if job.created_at is not None else None
        last_autorun = datetime.fromtimestamp(
            job.last_autorun).strftime('%Y-%m-%d %H:%M:%S') if job.last_autorun is not None else None
        print(f"{job.user_id}: {job.name}")
        print(f" - scheduled_time: {scheduled_time}")
        print(f" - created_at: {created_at}")
        print(f" - last_autorun: {last_autorun}")
        print("\n")

        # print(job.to_dict())
        # for ingredient in job.recipe:
        #     print(f"  Ingredient {ingredient.id}: {ingredient.playlist.get('name')}")

    print(len(jobs), "jobs found")


def inspect_users(users=None):

    if users is None:
        users = User.query.all()  # Get all users in the database

    for user in users:
        print(
            f"User {user.id} | job.id {user.jobs[0].id} | last_updated {user.last_updated} | token {user.token}")
        # print(user.token)
        # for job in user.jobs:
        #     print(f"  Job {job.id}: {job.name}")

    print(len(users), "users found")


def inspect_tokens():
    tokens = Token.query.all()  # Get all tokens in the database

    for token in tokens:
        print(token.token_info)


def test_job(job_id=rivers_job_id, user_id=rivers):
    data_service = DataService()

    # user = User.query.filter_by(id=user_id).first()
    # token = user.token

    # Initialize spotipy.Spotify directly
    spotify = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope="playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played"
        )
    )
    job_service = JobService(data_service, spotify)

    job_service.process(spotify, job_id, user_id)


def test_scheduled_jobs():
    data_service = DataService()
    spotify_service = SpotifyService(
        os.getenv('SPOTIFY_CLIENT_ID'),
        os.getenv('SPOTIFY_CLIENT_SECRET'),
        os.getenv('SPOTIFY_REDIRECT_URI')
    )

    job_service = JobService(data_service, spotify_service)

    job_service.process_scheduled_jobs()


def main():
    app = create_app()  # Create your Flask app
    with app.app_context():  # Push the app context
        # remove_duplicate_ingredients()
        # inspect_jobs()
        # users = users = [User.query.filter_by(id=katie_id).first()]
        # inspect_users(users=users)
        # inspect_tokens()
        # test_job(user_id=katie_id, job_id=katie_job_id)
        test_job()
        # test_scheduled_jobs()


if __name__ == "__main__":
    main()
