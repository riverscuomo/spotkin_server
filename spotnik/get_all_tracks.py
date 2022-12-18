from spotnik.extract_id import extract_id
from spotnik.api import sample_playlist_tracks


def get_all_tracks(data, job, spotify):
    """
    This function will get the tracks from the playlists the user has specified in data/add_list.csv
    """
    target_playlist_name = job["name"]
    print(
        f"Getting tracks from the playlists earmarked for the {target_playlist_name} playlist..."
    )
    my_picks = []

    for row in data:

        try:
            # How many songs you want to grab from the source playlist for this target playlist
            quantity = int(row[target_playlist_name])
        except KeyError:
            print(
                f"Error: '{target_playlist_name}' not found in the header row of add_list.csv"
            )
            exit()

        if quantity is None or quantity == "" or quantity < 1:
            # print("skipping row...")
            continue

        quantity = int(quantity)

        # parse the id of the playlist from whatever the user has entered in config.py
        playlist_id = extract_id(row)

        # for logging purposes
        playlist_name = row["Name"]

        new_tracks = sample_playlist_tracks(
            spotify,
            playlist_id,
            quantity,
            # skip_recents=skip_recents,
            name=playlist_name,
        )

        my_picks.extend(new_tracks)

    return my_picks


# # Some playlist you want to repeat songs until
# # x number of songs have gone by
# skip_recents = (
#     all_time_played_songs_ids[: row["Skip Recents"]]
#     if row["Skip Recents"] != ""
#     else None
# )
