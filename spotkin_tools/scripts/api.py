import os
import random
import spotipy
from spotipy import SpotifyOAuth, Spotify
try:
    from scripts.utils import *
except:
    from spotkin_tools.scripts.utils import *
from dotenv import load_dotenv

load_dotenv()

# SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
# SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
# SPOTIPY_REDIRECT_URL = "http://localhost:8080"
# scope = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played,user-top-read"
# SPOTIPY_USER = os.getenv("SPOTIPY_USER")


def get_spotify_client(refresh_token: str = None, timeout: int = 20) -> Spotify:
    log("[get_spotify] Creating Spotify client")
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URL = os.getenv("SPOTIFY_REDIRECT_URL")
    SPOTIFY_SCOPE = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played"

    print(SPOTIPY_REDIRECT_URL)
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URL,
        scope=SPOTIFY_SCOPE,
        cache_path=".cache-file"  # Optional: where to store the token info
    )

    client = spotipy.Spotify(auth_manager=auth_manager)

    print(client.current_user())

    return client


def get_spotify(timeout=20) -> spotipy.Spotify:
    log("[get_spotify] Creating Spotify client")
    print(SPOTIPY_REDIRECT_URL)

    # This code currently uses the deprecated username parameter.
    token = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URL,
        scope=scope,
        username=SPOTIPY_USER,
        requests_timeout=timeout,
    )

    spotify = spotipy.Spotify(auth_manager=token, requests_timeout=timeout)
    return spotify


def sample_playlist_tracks(spotify: spotipy.Spotify, playlist_id, limit, name):
    log(
        f"- sampling up to {limit} Spotify tracks from the playlist '{name}'... "
    )
    all_tracks = get_playlist_tracks(spotify, playlist_id)
    # remove tracks with None type ids
    all_tracks = [track for track in all_tracks if track["track"]
                  is not None and track["track"]["id"] is not None]
    return random.sample(all_tracks, min(limit, len(all_tracks)))


def get_playlist_tracks(spotify: spotipy.Spotify, playlist_id):
    """
    Returns all tracks in a given playlist.
    """
    results = spotify.playlist_tracks(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])
    return tracks


def get_artists_genres(spotify: spotipy.Spotify, artist_ids):
    log("- returning artist genres for artist ids...")
    chunks = divide_chunks(artist_ids, 50)
    artist_genres = []
    for chunk in chunks:
        result = spotify.artists(chunk)["artists"]
        for item in result:
            artist_id = item["id"]
            genres = item["genres"]
            artist_genre_object = {"artist_id": artist_id, "genres": genres}
            artist_genres.append(artist_genre_object)
    return artist_genres


def get_audio_features(spotify: spotipy.Spotify, track_ids):
    """
    Retrieves audio features for a list of track IDs from the Spotify API.

    Args:
        spotify: An instance of the `spotipy.Spotify` class representing the Spotify API client.
        track_ids: A list of track IDs for which to retrieve audio features.

    Returns:
        A dictionary mapping each track ID to its corresponding audio features, excluding any features that are None.

    Examples:
        spotify = spotipy.Spotify()
        track_ids = ["track1", "track2", "track3"]
        features = get_audio_features(spotify, track_ids)
        # Returns: {"track1": {"id": "track1", "feature": "data"}, "track2": {"id": "track2", "feature": "data"}, "track3": {"id": "track3", "feature": "data"}}
    """
    log("- returning get_audio_features track ids...")
    chunks = divide_chunks(track_ids, 100)
    audio_features = []
    for chunk in chunks:
        result = spotify.audio_features(chunk)
        audio_features.extend(iter(result))
    return {v["id"]: v for v in audio_features if v is not None}


def get_playlist_track_ids(spotify: spotipy.Spotify, playlist_id, limit, skip_recents=None, name=""):
    tracks = get_playlist_tracks(spotify, playlist_id, limit, name)
    return [x["track"]["id"] for x in tracks if x["track"] is not None]
