import os
import spotipy
import spotipy.util as util
from json.decoder import JSONDecodeError
from spotnik.utils import *

from rich import print

SPOTIFY_SCOPE = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played, ugc-image-upload"
SPOTIFY_SCOPE_WARNING = "signing into spotify...\nIf this program or another program with the same client_id\nhas changed scopes, you'll need to reauthorize each time.\nMake sure all programs have the same scope."
SPOTIFY_USER = os.getenv("SPOTIFY_USER")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URL = os.getenv("SPOTIFY_REDIRECT_URL")


def oauthStepTwo():
    from requests_oauthlib import OAuth2Session

    auth_url = "https://accounts.spotify.com/authorize"
    token_url = "https://accounts.spotify.com/api/token"

    scope = "playlist-modify-private"
    oauth = OAuth2Session(
        SPOTIFY_CLIENT_ID, redirect_uri=SPOTIFY_REDIRECT_URL, scope=scope
    )

    authorization_url, state = oauth.authorization_url(auth_url)

    print("Please go to %s and authorize access." % authorization_url)

    authorization_response = input("Enter the full callback URL")
    print(authorization_response)

    token = oauth.fetch_token(
        token_url,
        authorization_response=authorization_response,
        client_secret=SPOTIPY_CLIENT_SECRET,
    )
    print(token)


def get_spotify():
    log("get_spotify...")

    try:
        token = util.prompt_for_user_token(
            SPOTIFY_USER,
            redirect_uri="http://localhost:8080",
            scope=SPOTIFY_SCOPE,
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
        )
    except (AttributeError, JSONDecodeError):
        os.remove(f".cache-{SPOTIFY_USER}")
        token = util.prompt_for_user_token(
            SPOTIFY_USER,
            redirect_uri="http://localhost:8080",
            scope=SPOTIFY_SCOPE,
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
        )

    if token:
        spotify = spotipy.Spotify(auth=token)
    else:
        print(SPOTIFY_SCOPE_WARNING)
    return spotify


def get_playlist_tracks(spotify, playlist_id, limit, name):
    print(
        f"- returning a maximum of {limit} Spotify tracks from the playlist '{name}'..."  # with ID: {playlist_id}..."
    )
    results = spotify.playlist_tracks(playlist_id, limit=limit)
    return results["items"]


def get_artists_genres(spotify, artist_ids):
    print("- returning artist genres for artist ids...")
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


def get_audio_features(spotify, track_ids):
    print("- returning get_audio_features track ids...")
    chunks = divide_chunks(track_ids, 100)
    audio_features = []
    for chunk in chunks:
        result = spotify.audio_features(chunk)
        audio_features.extend(iter(result))
    return audio_features


def get_playlist_track_ids(spotify, playlist_id, limit, skip_recents=None, name=""):
    tracks = get_playlist_tracks(spotify, playlist_id, limit, name)
    return [x["track"]["id"] for x in tracks if x["track"] is not None]
