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

    description = f"{fact}..." + job["description"]

    log(f"Updating playlist description: {description}")

    spotify.user_playlist_change_details(
        spotify.me()["id"], job["playlist_id"], description=description
    )
