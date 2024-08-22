try:
    from scripts.api import sample_playlist_tracks
    from scripts.utils import log
except:
    from spotkin.scripts.api import sample_playlist_tracks
    from spotkin.scripts.utils import log


from concurrent.futures import ThreadPoolExecutor, as_completed


def get_playlist_tracks_wrapper(args):
    spotify, playlist_id, quantity, playlist_name = args
    return sample_playlist_tracks(spotify, playlist_id, quantity, name=playlist_name)


def get_all_tracks(job, spotify):
    """
    This function will get the tracks from the playlists the user has specified
    using parallel processing to speed up execution.
    """
    target_playlist_name = job["name"]
    log(
        f"Getting tracks from the playlists earmarked for the {target_playlist_name} playlist...")

    my_picks = []
    tasks = []

    # Prepare tasks for parallel execution
    for row in job["recipe"]:
        quantity = int(row["quantity"]) if row["quantity"] else None
        if quantity is None or quantity == "" or quantity < 1:
            continue

        playlist_id = row["source_playlist_id"]
        playlist_name = row["source_playlist_name"]

        tasks.append((spotify, playlist_id, quantity, playlist_name))

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_playlist = {executor.submit(
            get_playlist_tracks_wrapper, task): task for task in tasks}

        for future in as_completed(future_to_playlist):
            task = future_to_playlist[future]
            try:
                new_tracks = future.result()
                my_picks.extend(new_tracks)
            except Exception as exc:
                playlist_name = task[3]
                log(f"Playlist {playlist_name} generated an exception: {exc}")

    return my_picks

# def get_all_tracks(job, spotify):
#     """
#     This function will get the tracks from the playlists the user has specified
#     """
#     target_playlist_name = job["name"]
#     log(
#         f"Getting tracks from the playlists earmarked for the {target_playlist_name} playlist..."
#     )
#     my_picks = []

#     for row in job["recipe"]:
#         quantity = int(row["quantity"])

#         if quantity is None or quantity == "" or quantity < 1:
#             continue

#         # parse the id of the playlist from whatever the user has entered in config.py
#         playlist_id = row["source_playlist_id"]

#         # for logging purposes
#         playlist_name = row["source_playlist_name"]

#         new_tracks = sample_playlist_tracks(
#             spotify,
#             playlist_id,
#             quantity,
#             name=playlist_name,
#         )

#         my_picks.extend(new_tracks)

#     return my_picks


# # Some playlist you want to repeat songs until
# # x number of songs have gone by
# skip_recents = (
#     all_time_played_songs_ids[: row["Skip Recents"]]
#     if row["Skip Recents"] != ""
#     else None
# )
