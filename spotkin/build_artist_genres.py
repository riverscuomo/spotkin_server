from spotkin.scripts.api import get_artists_genres


def build_artist_genres(spotify, tracks):
    # list of artist ids to you can get the genre objects in one call
    artists = [track["artists"][0] for track in tracks]
    artist_ids = [artist["id"] for artist in artists]
    artist_ids = list(set(artist_ids))
    return get_artists_genres(spotify, artist_ids)