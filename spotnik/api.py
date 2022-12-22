import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotnik.utils import *
from rich import print
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_SCOPE = "playlist-modify-private, playlist-modify-public, user-library-read, playlist-read-private, user-library-modify, user-read-recently-played"
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


def get_spotify() -> spotipy.Spotify:
    log("get_spotify...")

    auth_manager=SpotifyOAuth(
        scope=SPOTIFY_SCOPE, 
        redirect_uri="http://localhost:8080", 
        client_id=SPOTIFY_CLIENT_ID, 
        client_secret=SPOTIPY_CLIENT_SECRET
    )

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    return spotify

def sample_playlist_tracks(spotify: spotipy.Spotify, playlist_id, limit, name):
    print(
        f"- sampling up to {limit} Spotify tracks from the playlist '{name}'... "
    )
    all_tracks = get_playlist_tracks(spotify, playlist_id)
    # remove tracks with None type ids
    all_tracks = [track for track in all_tracks if track["track"] is not None and track["track"]["id"] is not None]
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


def get_audio_features(spotify: spotipy.Spotify, track_ids):
    print("- returning get_audio_features track ids...")
    chunks = divide_chunks(track_ids, 100)
    audio_features = []
    for chunk in chunks:
        result = spotify.audio_features(chunk)
        audio_features.extend(iter(result))
    return {v["id"]: v for v in audio_features}


def get_playlist_track_ids(spotify: spotipy.Spotify, playlist_id, limit, skip_recents=None, name=""):
    tracks = get_playlist_tracks(spotify, playlist_id, limit, name)
    return [x["track"]["id"] for x in tracks if x["track"] is not None]
