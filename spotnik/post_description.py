import random
import re
import os
from rich import print
from spotnik.utils import *


def getFact():
    # get the random fact
    fact_path = os.path.join("spotnik", "data", "randomfacts.txt")
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
    fact = ""
    while not fact:
        fact = getFact()

    description = f"{fact}..." + job["description"]

    """ 
    MUST UPDATE SPOTIPY LIKE THIS:
    https://stackoverflow.com/questions/47028093/attributeerror-spotify-object-has-no-attribute-current-user-saved-tracks

    Still relevant? I don't know.
    """
    spotify.user_playlist_change_details(
        spotify.me()["id"], job["playlist_id"], description=description
    )
