def extract_id(row: dict):
    """
    Returns the playlist id if the full playlist url is provided
    """
    id = row["Playlist ID"]
    # print(id[:5])
    if id[:5] == "https":
        id = id.split("playlist/")[1]
        id = id.split("?")[0]
    return id
