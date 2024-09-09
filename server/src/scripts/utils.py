from server.src.models.models import Job
from server.database.database import db
from server.src.server import create_app


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


def main():
    app = create_app()  # Create your Flask app
    with app.app_context():  # Push the app context
        remove_duplicate_ingredients()


if __name__ == "__main__":
    main()
