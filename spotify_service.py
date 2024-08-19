
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyService:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def create_spotify_oauth(self):
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="user-library-read playlist-modify-public playlist-modify-private",
        )

    def refresh_token_if_expired(self, token_info):
        sp_oauth = self.create_spotify_oauth()
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(
                token_info['refresh_token'])
        return token_info

    def create_spotify_client(self, token_info):
        return spotipy.Spotify(auth=token_info['access_token'])
