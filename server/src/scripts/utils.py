import os
from server.src.models.models import Job, Token, User
from server.database.database import db
from server.src.server import create_app
from server.src.services.data_service import DataService
from server.src.services.job_service import JobService
from server.src.services.spotify_service import SpotifyService


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


def inspect_users():
    users = User.query.all()  # Get all users in the database

    for user in users:
        print(f"User {user.id}: {user.last_updated}")
        print(user.token)
        # for job in user.jobs:
        #     print(f"  Job {job.id}: {job.name}")

    print(len(users), "users found")


def inspect_tokens():
    tokens = Token.query.all()  # Get all tokens in the database

    for token in tokens:
        print(token.token_info)


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
        # inspect_users()
        # inspect_tokens()
        test_scheduled_jobs()


if __name__ == "__main__":
    main()
