from importlib import import_module
from re import X
from spotnik.get_all_tracks import get_all_tracks
from spotnik.bans import *
import random
from spotnik.post_description import *
from spotnik.api import *
from rich import print
from spotnik.utils import *
import csv
import os
from dotenv import load_dotenv

load_dotenv()


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

        # make list of just the track objects while also eliminating duplicates
        tracks = list({v["track"]["id"]: v["track"] for v in tracks}.values())

        track_ids = [x["id"] for x in tracks]

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

        for chunk in (updated_tracks[i:i+limit] for i in range(0, len(updated_tracks), limit)):
            result = spotify.user_playlist_add_tracks(
                spotify.me()["id"], job["playlist_id"], chunk
            )

        # change the playlist description to a random fact
        post_description(spotify, job)

    return "Success!"


def build_artist_genres(spotify, tracks):
    # list of artist ids to you can get the genre objects in one call
    artists = [track["artists"][0] for track in tracks]
    artist_ids = [artist["id"] for artist in artists]
    artist_ids = list(set(artist_ids))
    return get_artists_genres(spotify, artist_ids)


if __name__ == "__main__":

    main()
