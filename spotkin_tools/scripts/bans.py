try:
    from scripts.utils import *
except:
    from spotkin_tools.scripts.utils import *


class FilterTool:
    """Determines whether songs belong in the playlist or not based on a job."""

    def __init__(self, job) -> None:
        self.job = job

    def is_banned(self, artist_genres=[], album_id=None, artist_id=None, artist_name=None, track_name=None, track=None, track_id=None,  audio_features=None, ban_skits=False):
        return self._is_banned_by_genre(artist_genres, artist_name, track_name) or \
            self._is_banned_by_skit(track_name, artist_name) or \
            self._is_banned_by_audio_features(
                track_name, artist_name, track, audio_features) or \
            self.is_banned_by_album_id(album_id, artist_name, track_name) or \
            self._is_banned_by_artist_id(artist_id, track_name) or \
            self._is_banned_by_track_id(track_id, artist_name, track_name)

    def _is_banned_by_artist_id(self, artist_id, track_name):
        # print("_is_banned_by_artist_id")

        if "banned_artists" not in self.job:
            return False

        banned_artists = [x["id"] for x in self.job["banned_artists"]]

        if artist_id and artist_id in banned_artists:
            log(
                f"Removed {track_name} because {artist_id} is in this playlist's banned artist ids"
            )
            return True
        return False

    def is_banned_by_album_id(self, album_id, artist_name, track_name):
        # print("_is_banned_by_album_id")

        if "banned_albums" not in self.job:
            return False

        banned_albums = [x["id"] for x in self.job["banned_albums"]]

        if album_id and album_id in banned_albums:
            log(
                f"Removed {track_name} by {artist_name} because {album_id} is in this playlist's banned album ids"
            )
            return True
        return False

    # def _is_banned_by_artist_name(self, artist_name, track_name):
    #     # print("_is_banned_by_artist_name")

    #     if "banned_artist_names" not in self.job:
    #         return False

    #     banned_artist_names_lowercase = [
    #         str(x.lower()) for x in self.job["banned_artist_names"]]

    #     if artist_name.lower() in banned_artist_names_lowercase:
    #         log(
    #             f"Removed {track_name} by {artist_name} because {artist_name} is in this playlist's banned artist names"
    #         )
    #         return True
    #     return False

    def _is_banned_by_audio_features(self, track_name, artist_name, track, audio_features):
        # Properties no longer being checked as per requirements:
        # - min_acousticness, max_acousticness
        # - min_danceability, max_danceability
        # - min_duration, max_duration
        # - min_energy, max_energy
        # - min_popularity, max_popularity
        
        # These properties are no longer settable, so we ignore them even if they're in the job object
        
        # If no condition bans the track
        return False

    def _is_banned_by_genre(self, artist_genres, artist_name, track_name):
        # print("_is_banned_by_genre")

        if "banned_genres" not in self.job or self.job["banned_genres"] is None or artist_genres is None:
            return False

        # want to try being more aggressive here.
        # Now a banned genre 'rap' will reject 'Cali rap', 'trap' and 'rap metal' etc.
        elif (
            # if any of the banned genres are in the artist's genre
            any(
                banned_genre in artist_genres for banned_genre in self.job["banned_genres"])
            and artist_name not in self.job["exceptions_to_banned_genres"]
        ):
            log(
                f"Removed {track_name} by {artist_name} because genre {artist_genres} is in this playlist's banned genres"
            )
            return True
        return False

    def _is_banned_by_skit(self, track_name, artist_name):
        """ Check if the track is a skit """

        if "ban_skits" not in self.job or not self.job["ban_skits"]:
            return False

        elif "skit" in track_name.lower():
            log(
                f"Removed {track_name} by {artist_name} because it is a skit"
            )
            return True

    # def _is_banned_by_song_title(self, artist_name, track_name):
    #     # print("_is_banned_by_song_title")

    #     if "banned_song_titles" not in self.job:
    #         return False

    #     banned_song_titles_lowercase = [
    #         str(x.lower()) for x in self.job["banned_song_titles"]]

    #     if str(track_name).lower() in banned_song_titles_lowercase:
    #         log(
    #             f"Removed {track_name} by {artist_name} because {track_name} is in this playlist's banned song titles"
    #         )
    #         return True
    #     return False

    def _is_banned_by_track_id(self, track_id, artist_name, track_name):
        # print("_is_banned_by_track_id")

        if "banned_tracks" not in self.job:
            return False

        banned_tracks = [x["id"] for x in self.job["banned_tracks"]]

        if track_id in banned_tracks:
            log(
                f"Removed {track_name} by {artist_name} because {track_id} is in this playlist's banned track_ids"
            )
            return True
        return False

    def _is_banned_by_track_popularity(self, track_id, artist_name, track_name):
        # print("_is_banned_by_track_id")

        if "banned_track_popularity" not in self.job:
            return False

        elif track_id in self.job["banned_track_popularity"]:
            log(
                f"Removed {track_name} by {artist_name} because {track_id} is in this playlist's banned track_ids"
            )
            return True
        return False

    def _is_banned_by_track_duration(self, track_id, artist_name, track_name):
        # print("_is_banned_by_track_id")

        if "banned_track_duration" not in self.job:
            return False

        elif track_id in self.job["banned_track_duration"]:
            log(
                f"Removed {track_name} by {artist_name} because {track_id} is in this playlist's banned track_ids"
            )
            return True
        return False
