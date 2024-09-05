import spotipy
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlencode

class SpotifyService:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = 'https://accounts.spotify.com/authorize'
        self.token_url = 'https://accounts.spotify.com/api/token'

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

    def get_auth_url(self):
        sp_oauth = self.create_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        return auth_url

    def exchange_code_for_token(self, code):
        sp_oauth = self.create_spotify_oauth()
        token_info = sp_oauth.get_access_token(code)
        return token_info

    def refresh_access_token(self, refresh_token):
        sp_oauth = self.create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(refresh_token)
        return token_info