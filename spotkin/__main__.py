from datetime import datetime
from re import X
from time import sleep

from .scripts.process_job import process_job
from .scripts.bans import *
from .scripts.post_description import *
from .scripts.api import *
from .scripts.utils import *

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
