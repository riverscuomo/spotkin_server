from importlib import import_module
from re import X
from spotnik.get_all_tracks import get_all_tracks
from spotnik.bans import *
import random
from spotnik.post_description import *
from spotnik.update_cover import *
from spotnik.api import *
from rich import print

# from spotnik.config import ADD_LIST_FILE
# from spotnik.config import JOBS_FILE
from spotnik.utils import *
from dotenv import load_dotenv, find_dotenv
import csv
import os
from dotenv import dotenv_values

# config = dotenv_values(".env")
# print(config)
load_dotenv()
# print(load_dotenv(find_dotenv()))
# print(JOBS_FILE)

JOBS_FILE_PATH = os.getenv("JOBS_FILE_PATH")
ADD_LIST_FILE_PATH = os.getenv("ADD_LIST_FILE_PATH")
# print(JOBS_FILE)
# print(ADD_LIST_FILE)

# ADD_LIST_FILE_PATH = r"


def get_data():
    log("getting the user's add list from csv file...")
    with open(ADD_LIST_FILE_PATH) as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
    return data


def import_jobs():

    log("importing jobs from file...")

    try:
        return import_module(f"{JOBS_FILE_PATH}", package="spotnik").jobs
    except ValueError as e:
        print(f"Error importing from fiat file: {JOBS_FILE_PATH} - {e}")


def main():

    log("spotnik.setup main...")

    spotify = get_spotify()

    jobs = import_jobs()

    data = get_data()

    for job in jobs:

        log(f"Spotnik playlist '{job['name']}'")

        tracks = get_all_tracks(data, job, spotify)

        updated_tracks = []

        tracks = list({v["track"]["id"]: v["track"] for v in tracks}.values())

        track_ids = [x["id"] for x in tracks]

        audio_features = get_audio_features(spotify, track_ids)
        artists_genres = build_artist_genres(spotify, tracks)

        # Cull banned items from your list
        for track in tracks:

            track_id = track["id"]
            track_name = track["name"]
            artist_id = track["artists"][0]["id"]
            artist_name = track["artists"][0]["name"]
            artist_genre = next(
                (x for x in artists_genres if x["artist_id"] == artist_id), None
            )

            if is_banned_by_genre(job, artist_genre, artist_name, track_name):
                continue

            if is_banned_by_track_id(job, track_id, artist_name, track_name):
                continue

            if is_banned_by_artist_name(job, artist_name, track_name):
                continue

            if is_banned_by_song_title(job, artist_name, track_name):
                continue

            if is_banned_by_low_energy(
                job, track_name, artist_name, track, audio_features
            ):
                continue

            updated_tracks.append(track["id"])

        random.shuffle(updated_tracks)

        limit = 100 - len(job["last_track_ids"])

        if len(updated_tracks) > limit:

            print(len(updated_tracks))
            updated_tracks = updated_tracks[:limit]

        # if you've specify a track or tracks to always add at the end (for easy access, for example,
        # nature sounds or white noise)
        updated_tracks.extend(job["last_track_ids"])

        print("updating spotify playlist")
        result = spotify.user_playlist_replace_tracks(
            SPOTIFY_USER, job["playlist_id"], updated_tracks
        )

        # change the playlist description to a random fact
        post_description(spotify, job)

        # change the playlist cover to a random predefined image
        update_cover(spotify, job)

    return "Success!"


def build_artist_genres(spotify, tracks):
    # list of artist ids to you can get the genre objects in one call
    artists = [track["artists"][0] for track in tracks]
    artist_ids = [artist["id"] for artist in artists]
    artist_ids = list(set(artist_ids))
    return get_artists_genres(spotify, artist_ids)


if __name__ == "__main__":

    main()
