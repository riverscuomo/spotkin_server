from spotnik.utils import *


def is_banned_by_artist_name(job, artist_name, track_name):

    if "banned_artist_names" not in job:
        return False

    banned_artist_names_lowercase = [str(x.lower()) for x in job["banned_artist_names"]]

    if artist_name.lower() in banned_artist_names_lowercase:
        log(
            f"Removed {track_name} by {artist_name} because {artist_name} is in this playlist's banned artist names"
        )
        return True
    return False


def is_banned_by_genre(job, artist_genre, artist_name, track_name):

    if "banned_genres" not in job or artist_genre is None:
        return False

    elif (
        artist_genre in job["banned_genres"]
        and not artist_name in job["exceptions_to_banned_genres"]
    ):
        log(
            f"Removed {track_name} by {artist_name} because genre {artist_genre} is in this playlist's banned genres"
        )
        return True
    return False


def is_banned_by_low_energy(job, track_name, artist_name, track, audio_features):
    """Useful for workout playlists"""

    if "remove_low_energy" not in job or job["remove_low_energy"] is False:
        return False

    audio_feature = next((x for x in audio_features if x["id"] == track["id"]), None)

    loudness = audio_feature["loudness"]
    energy = audio_feature["energy"]
    speechiness = audio_feature["speechiness"]
    acousticness = audio_feature["acousticness"]

    if loudness < -15:
        print(f"- {track_name} by {artist_name} banned for low loudness: {loudness}")
        return True

    # danceability =  audio_feature["danceability"]

    elif energy < 0.51:
        print(f"- {track_name} by {artist_name} banned for low energy: {energy}")
        return True

    elif acousticness > 0.42:
        print(
            f"- {track_name} by {artist_name} banned for high acousticness: {acousticness}"
        )
        return True
    # instrumentalness =  audio_feature["instrumentalness"]
    # liveness =  audio_feature[{} banned for iveness"]
    # tempo_spotify =  audio_feature["tempo"]
    # print(audio_feature["id"],loudness,danceability,energy,speechiness,acousticness,instrumentalness,liveness,tempo_spotify)
    # if energy > 0.5:
    else:
        return False


def is_banned_by_song_title(job, artist_name, track_name):

    if "banned_song_titles" not in job:
        return False

    banned_song_titles_lowercase = [str(x.lower()) for x in job["banned_song_titles"]]

    if str(track_name).lower() in banned_song_titles_lowercase:
        log(
            f"Removed {track_name} by {artist_name} because {track_name} is in this playlist's banned song titles"
        )
        return True
    return False


def is_banned_by_track_id(job, track_id, artist_name, track_name):

    if "banned_track_ids" not in job:
        return False

    elif track_id in job["banned_track_ids"]:
        log(
            f"Removed {track_name} by {artist_name} because {track_id} is in this playlist's banned track_ids"
        )
        return True
    return False


# def get_fiat_sheet_bans(sheet):

#     # headerRange = "A1:ZZ1"

#     # banned_artist_names = getColValues(sheet, headerRange, "artist_name")
#     # # print(banned_artist_names)
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
