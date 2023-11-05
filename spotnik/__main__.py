from importlib import import_module
from re import X
from spotnik.scripts.get_all_tracks import get_all_tracks
from spotnik.scripts.bans import *
import random
from spotnik.scripts.post_description import *
from spotnik.scripts.api import *
from rich import print
from spotnik.scripts.utils import *
import csv
import os
from dotenv import load_dotenv
import gspreader
import gspread

load_dotenv()

print("spotnik.setup main...")


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
    data = settings_sheet.get_all_records()
    # target_playlist_names = list()

    jobs = [{"name": x} for x in list(data[0].keys())[1:]]
    settings = [x["setting"] for x in data]

    # print(jobs)
    # print(settings)

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

    return jobs


def build_artist_genres(spotify, tracks):
    # list of artist ids to you can get the genre objects in one call
    artists = [track["artists"][0] for track in tracks]
    artist_ids = [artist["id"] for artist in artists]
    artist_ids = list(set(artist_ids))
    return get_artists_genres(spotify, artist_ids)


def main():

    log("spotnik.setup main...")

    spotify = get_spotify()

    # jobs = import_jobs()
    # print(jobs[0])

    # data = get_data()

    jobs = get_jobs_with_their_settings()
    
    jobs = get_recipes_for_each_job(jobs)

    # print(jobs)

    for job in jobs:

        log(f"Spotnik playlist '{job['name']}'")
        # log(f"Spotnik playlist 'Rivers Radio'")

        tracks = get_all_tracks(job, spotify)

        updated_tracks = []

        # make list of just the track objects while also eliminating duplicates and empty tracks
        tracks = list({v["track"]["id"]: v["track"] for v in tracks }.values())

        track_ids = [x["id"] for x in tracks]
        # print(track_ids)

        audio_features = get_audio_features(spotify, track_ids)
        artists_genres = build_artist_genres(spotify, tracks)
        filter = PlaylistFilter(job, audio_features)

        # Cull banned items from your list
        for track in tracks:

            track_id = track["id"]
            track_name = track["name"]
            artist_id = track["artists"][0]["id"]
            artist_name = track["artists"][0]["name"]
            artist_genre = next(
                (x for x in artists_genres if x["artist_id"] == artist_id), None
            )

            if filter.is_banned(artist_genre, artist_name, track_name, track_id, track):
                continue

            updated_tracks.append(track["id"])

        random.shuffle(updated_tracks)

        # if you've specify a track or tracks to always add at the end (for easy access, for example,
        # nature sounds or white noise)
        updated_tracks.extend(job["last_track_ids"])

        

        print("updating spotify playlist")
        # empty playlist
        result = spotify.user_playlist_replace_tracks(
            spotify.me()["id"], job["playlist_id"], []
        )

        limit = 100

        print(updated_tracks)

        for chunk in (updated_tracks[i:i+limit] for i in range(0, len(updated_tracks), limit)):
            result = spotify.user_playlist_add_tracks(
                spotify.me()["id"], job["playlist_id"], chunk
            )

        # change the playlist description to a random fact
        post_description(spotify, job)

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
#         return import_module(f"{JOBS_FILE_PATH}", package="spotnik").jobs
#     except ValueError as e:
#         print(f"Error importing from fiat file: {JOBS_FILE_PATH} - {e}")
