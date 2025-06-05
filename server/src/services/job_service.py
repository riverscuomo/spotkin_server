import datetime
import os
from server.src.models.models import Ingredient, Job, Token, User
from server.src.services import spotify_service
from spotkin_tools.scripts.process_job import process_job as tools_process_job
import time
import spotipy
from flask import Response, jsonify
from server.src.models.models import db
from rich import print
import uuid


class JobService:
    def __init__(self, data_service, spotify_service):
        self.data_service = data_service
        self.spotify_service = spotify_service

    def add_job(self, user_id, job_data):
        new_job = Job(
            user_id=user_id,
            playlist_id=job_data['playlist_id'],
            name=job_data['name'],
            scheduled_time=job_data.get('scheduled_time'),
            description=job_data.get('description'),
            ban_skits=job_data.get('ban_skits', False)
        )

        for ingredient_data in job_data.get('recipe', []):
            ingredient = Ingredient(
                playlist_id=ingredient_data['source_playlist_id'],
                playlist_name=ingredient_data['source_playlist_name'],
                quantity=ingredient_data['quantity']
            )
            new_job.ingredients.append(ingredient)

        db.session.add(new_job)
        db.session.commit()
        return new_job.to_dict()

    def convert_server_job_to_tools_job(self, job):
        """ Convert a Job model instance to a dictionary that can be used by the original tools script. """
        job_dict = job.to_dict()

        job_dict['playlist_id'] = job_dict['target_playlist']['id']

        for ingredient in job_dict['recipe']:
            ingredient['source_playlist_id'] = ingredient['playlist']['id']
            ingredient['source_playlist_name'] = ingredient['playlist']['name']
        return job_dict
    # Ensure the user exists before creating/updating a job

    def delete_job(self, user_id, job_index):
        self.data_service.delete_job(user_id, job_index)

    def ensure_user_exists(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            # Create user if they don't exist (adjust as necessary for your user fields)
            new_user = User(id=user_id)  # Example
            db.session.add(new_user)
            db.session.commit()

    def get_jobs(self, user_id):
        print(f"Getting jobs for user: {user_id}")
        jobs = Job.query.filter_by(user_id=user_id).all()
        print([job.name for job in jobs])
        return [job.to_dict() for job in jobs]

    def get_schedule(self):
        all_jobs = self.data_service.get_all_data()
        schedule_info = {
            user_id: {
                'jobs': [{
                    'name': job.get('name', 'Unnamed job'),
                    'scheduled_time': job['scheduled_time'],
                    'last_processed': job.get('last_processed', 'Never'),
                } for job in user_data.get('jobs', [])]
            } for user_id, user_data in all_jobs.items()
        }
        return jsonify({"status": "success", "schedule": schedule_info})

    def process(self, spotify, job_id, user_id):
        try:
            job = Job.query.filter_by(id=job_id, user_id=user_id).first()

            if not job:
                return {'status': 'error', 'message': 'Job not found.'}, 404

            job_dict = self.convert_server_job_to_tools_job(job)
            if tools_process_job(spotify, job_dict):
                return {'status': 'success', 'message': 'Job processed successfully.'}, 200
            else:
                return {'status': 'error', 'message': 'Job processing failed.'}, 500
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    def process_job(self, job_id, request):
        """ When the user clicks 'Update' in the UI, this function is called to process the job immediately. """

        if 'Authorization' not in request.headers:
            return jsonify({'status': 'error', 'message': 'Authorization header is missing.'}), 401

        access_token = request.headers['Authorization'].split(' ')[1]

        try:
            # Create Spotify client with access token
            spotify = spotipy.Spotify(auth=access_token)

            # Get the current user
            user = spotify.current_user()
            user_id = user['id']

            # Check if the token already exists for the user
            if token := Token.query.filter_by(user_id=user_id).first():
                # Update the token info in the database
                token.token_info = {
                    'access_token': access_token,
                    # Save refresh token if passed from client
                    'refresh_token': request.json.get('refresh_token'),
                    # Save expires_at if passed from client
                    'expires_at': request.json.get('expires_at')
                }
            else:
                # Create new token entry if it doesn't exist
                token = Token(
                    user_id=user_id,
                    token_info={
                        'access_token': access_token,
                        'refresh_token': request.json.get('refresh_token'),
                        'expires_at': request.json.get('expires_at')
                    }
                )
                db.session.add(token)

            # Commit the token information
            db.session.commit()

            data, code = self.process(spotify, job_id, user_id)

            if code != 200:
                return jsonify({'status': 'error', 'message': data['message']}), code
            else:

                return jsonify({
                    "message": "Processed successfully",
                    "status": "success"
                }), 200

        except spotipy.exceptions.SpotifyException as e:
            return jsonify({'status': 'error', 'message': str(e)}), 401

    def process_scheduled_jobs(self):
        print('process_scheduled_jobs...')

        now = datetime.datetime.now(datetime.timezone.utc)
        now_timestamp = now.timestamp()
        current_hour = now.hour

        jobs = Job.query.all()  # Fetch all jobs

        for job in jobs:
            scheduled_time = job.scheduled_time
            user_id = job.user_id

            if scheduled_time == current_hour:

                # Convert job.last_updated to seconds if it's in milliseconds
                if job.last_updated:
                    if job.last_updated > 1e12:  # Threshold to distinguish between ms and s
                        job_last_updated_seconds = job.last_updated / 1000
                    else:
                        job_last_updated_seconds = job.last_updated

                    # Check if job.last_updated is in the future
                    if job_last_updated_seconds > now_timestamp:
                        print(
                            f"Job {user_id} has a last_updated timestamp in the future.")
                        continue

                    # Calculate the time difference
                    time_difference = now_timestamp - job_last_updated_seconds

                    # Skip jobs not updated in last 21 days
                    if time_difference > 1814400:
                        print(
                            f"Skipping job for user: {user_id} because it hasn't been updated in the last 21 days")
                        continue
                else:
                    print(f"Job {user_id} has no last_updated timestamp.")
                    continue  # Decide whether to skip or process jobs without a last_updated timestamp

                print(
                    f"Processing job for user: {user_id} because scheduled time {scheduled_time} matches current hour {current_hour}")

                # Retrieve the token for the user
                token = Token.query.filter_by(user_id=user_id).first()
                if not token or not token.token_info.get('access_token'):
                    print(f"No valid token found for user: {user_id}")
                    continue

                # Refresh the token if needed
                token_info_with_new_refresh_token = self.spotify_service.refresh_token_if_expired(
                    token.token_info)

                # Update the token info in the database
                token.token_info = token_info_with_new_refresh_token
                db.session.commit()

                # Create Spotify client using the refreshed token
                spotify = self.spotify_service.create_spotify_client(
                    token.token_info
                )

                # Call the process method
                data, status_code = self.process(spotify, job.id, user_id)

                if status_code != 200:
                    message = str(data['message'])
                    raise Exception(
                        f"Job processing failed with message: {message}")
                else:
                    print(f"Job processed successfully: {data['message']}")

                # Update last_autorun timestamp
                job.last_autorun = now.timestamp()
                db.session.commit()

                print(f"Job processed successfully for user: {user_id}")

            else:
                f"Skipping job for user: {job.user_id} because scheduled time {scheduled_time} does not match current hour {current_hour}"

        def get_schedule(self):
            all_jobs = self.data_service.get_all_data()
            schedule_info = {
                user_id: {
                    'jobs': [{
                        'name': job.get('name', 'Unnamed job'),
                        'scheduled_time': job['scheduled_time'],
                        'last_processed': job.get('last_processed', 'Never'),
                    } for job in user_data.get('jobs', [])]
                } for user_id, user_data in all_jobs.items()
            }
            return jsonify({"status": "success", "schedule": schedule_info})

        def update_job(self, job_id, updated_job_data, user_id):
            print(f"Updating job {job_id} for user {user_id}")
            # ensure the user is in the db
            self.ensure_user_exists(user_id)
            # Try to find the existing job by job_id and user_id
            job = Job.query.filter_by(id=job_id, user_id=user_id).first()

            if job:
                # Update the existing job with new data
                for key, value in updated_job_data.items():
                    if hasattr(job, key):
                        if key == 'recipe':
                            # Handle the 'recipe' separately since it's a relationship
                            job.recipe = []  # Clear existing ingredients

                            # Use a set to track playlist IDs for preventing duplicate ingredients
                            added_playlists = set()

                            for ingredient_data in value:
                                ingredient = Ingredient.from_dict(
                                    ingredient_data)
                                # Use the playlist id to determine uniqueness
                                playlist_id = ingredient.playlist.get('id')

                                if playlist_id not in added_playlists:
                                    job.recipe.append(ingredient)
                                    added_playlists.add(playlist_id)
                                    # Update the last_updated timestamp
                                    job.last_updated = int(time.time())
                                else:
                                    print(
                                        f"Duplicate playlist detected: {playlist_id}, skipping.")
                        else:
                            # Update scalar attributes
                            setattr(job, key, value)
                    else:
                        print(
                            f"Server Job model does not have attribute: {key}")
            else:
                # Create a new job if it doesn't exist
                job = Job.from_dict(updated_job_data)
                job.id = job_id  # Assign the provided job_id
                job.user_id = user_id  # Ensure the job is linked to the correct user
                # Update the last_updated timestamp
                job.last_updated = int(time.time())
                db.session.add(job)

            db.session.commit()  # Commit the changes to the database
            return job.to_dict()  # Return the job as a dictionary

        def update_job_schedule(self, data):
            user_id = data['user_id']
            new_time = data['new_time']
            job_name = data.get('job_name', None)

            all_jobs = self.data_service.get_all_data()
            if user_id in all_jobs:
                for job in all_jobs[user_id]['jobs']:
                    if job_name is None or job['name'] == job_name:
                        job['scheduled_time'] = new_time
                self.data_service.store_job_and_token(
                    user_id, all_jobs[user_id]['jobs'], all_jobs[user_id]['token'])
                return jsonify({"status": "updated", "new_time": new_time})
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404

    def get_job_by_id(self, job_id):
        """
        Get a job by its ID
        
        Parameters:
        - job_id: The ID of the job to retrieve
        
        Returns: Job object or None if not found
        """
        return Job.query.filter_by(id=job_id).first()
    
    def add_source_from_recommendation(self, job_id, source_type, item_id, item_name, user_id):
        """
        Add a source to a job based on recommendations from a track, artist, or album
        
        Parameters:
        - job_id: ID of the job to update
        - source_type: 'track', 'artist', or 'album'
        - item_id: Spotify ID of the item
        - item_name: Name for display purposes
        - user_id: ID of the user making the request
        
        Returns: Updated job object
        """
        # Get the job to update
        job = Job.query.filter_by(id=job_id, user_id=user_id).first()
        if not job:
            raise ValueError(f"Job not found with ID: {job_id}")
        
        # Get token for the user
        token = Token.query.filter_by(user_id=user_id).first()
        if not token or not token.token_info.get('access_token'):
            raise ValueError(f"No valid token found for user: {user_id}")
            
        # Try to refresh the token if needed
        try:
            token_info_with_refresh = self.spotify_service.refresh_token_if_expired(token.token_info)
            # Update token in database if refreshed
            if token_info_with_refresh != token.token_info:
                token.token_info = token_info_with_refresh
                db.session.commit()
                
            # Create Spotify client with refreshed token
            spotify = spotipy.Spotify(auth=token.token_info.get('access_token'))
        except Exception as e:
            print(f"Error refreshing token: {e}")
            raise ValueError(f"Failed to refresh Spotify access token: {str(e)}")
            
        
        # Initialize tracks list that we'll populate
        tracks = []
        
        try:
            if source_type == 'track':
                # Verify track exists
                track = spotify.track(item_id)
                track_name = track['name']
                name_prefix = f"Based on track: {item_name}"
                print(f"Track validated: {track_name}")
                
                # Get the artist of the track
                artist_id = track['artists'][0]['id']
                
                try:
                    # Try to get top tracks from the artist's country
                    artist_top_tracks = spotify.artist_top_tracks(artist_id, country='US')
                    tracks = artist_top_tracks['tracks']
                    print(f"Found {len(tracks)} top tracks from artist")
                except Exception as e:
                    print(f"Error getting artist top tracks: {e}")
                    # Fallback to just using the track itself
                    tracks = [track]
                
            elif source_type == 'artist':
                # Verify artist exists
                artist = spotify.artist(item_id)
                artist_name = artist['name']
                print(f"Artist validated: {artist_name}")
                
                # Try to find "This Is [Artist]" playlist first
                search_query = f"This Is {artist_name}"
                print(f"Searching for '{search_query}'")
                spotify_playlist = None
                
                try:
                    results = spotify.search(q=search_query, type='playlist', limit=5)
                    playlists = results.get('playlists', {}).get('items', [])
                    
                    # Look through results for an official "This Is" playlist
                    for playlist in playlists:
                        if playlist['name'].lower().startswith('this is') and artist_name.lower() in playlist['name'].lower():
                            # Check if it's from Spotify
                            if playlist['owner']['id'] == 'spotify':
                                print(f"Found official 'This Is {artist_name}' playlist!")
                                spotify_playlist = playlist
                                break
                    
                    if spotify_playlist:
                        # Use the Spotify "This Is" playlist directly
                        playlist_data = {
                            "id": spotify_playlist['id'],
                            "name": spotify_playlist['name'],
                            "uri": spotify_playlist['uri'],
                            "images": spotify_playlist.get('images', []),
                            "description": spotify_playlist.get('description', f"Spotify's This Is {artist_name} playlist"),
                            "is_official_spotify_playlist": True  # Add a flag to mark this as official
                        }
                        
                        ingredient_data = {
                            'id': str(uuid.uuid4()),
                            'job_id': str(job.id),
                            'playlist': playlist_data,
                            'quantity': 2  # Default quantity
                        }
                        
                        # Create and add ingredient
                        ingredient = Ingredient.from_dict(ingredient_data)
                        job.recipe.append(ingredient)
                        
                        # Update job timestamp
                        job.last_updated = int(time.time())
                        
                        # Save to database
                        db.session.commit()
                        
                        # Return early with the updated job
                        print(f"Added official 'This Is {artist_name}' playlist directly to job")
                        return job.to_dict()
                
                except Exception as e:
                    print(f"Error searching for or using 'This Is' playlist: {e}")
                
                # If no "This Is" playlist was found, fallback to creating our own playlist
                print(f"No official 'This Is {artist_name}' playlist found. Creating custom playlist.")
                name_prefix = f"Based on artist: {item_name}"
                
                # Get the artist's top tracks
                try:
                    # Get the artist's top tracks - specify US as the country
                    artist_top_tracks = spotify.artist_top_tracks(item_id, country='US')
                    tracks = artist_top_tracks['tracks']
                    print(f"Found {len(tracks)} top tracks for {artist_name}")
                except Exception as e:
                    print(f"Error getting top tracks: {e}")
                    raise ValueError(f"Could not get top tracks for artist: {str(e)}")
                
                # Try to get related artists if we need more tracks
                if len(tracks) < 15:
                    try:
                        print(f"Getting related artists for {artist_name}")
                        related_artists = spotify.artist_related_artists(item_id)
                        related_count = 0
                        
                        for related in related_artists['artists'][:3]:  # Add tracks from up to 3 related artists
                            try:
                                related_top = spotify.artist_top_tracks(related['id'], country='US')
                                if related_top and 'tracks' in related_top:
                                    print(f"Adding tracks from related artist: {related['name']}")
                                    tracks.extend(related_top['tracks'][:5])  # Add up to 5 tracks per related artist
                                    related_count += 1
                            except Exception as e:
                                print(f"Could not get top tracks for related artist {related['name']}: {e}")
                        print(f"Added tracks from {related_count} related artists")
                    except Exception as e:
                        print(f"Error getting related artists: {e}")
                        # Continue without related artists
                
            elif source_type == 'album':
                # Verify album exists
                album = spotify.album(item_id)
                album_name = album['name']
                name_prefix = f"Based on album: {item_name}"
                print(f"Album validated: {album_name}")
                
                # Get all tracks from the album
                try:
                    tracks = []
                    album_tracks = spotify.album_tracks(item_id)
                    
                    # Process initial results
                    track_items = album_tracks['items']
                    for track in track_items:
                        if track.get('id'):
                            # Get full track data
                            try:
                                full_track = spotify.track(track['id'])
                                tracks.append(full_track)
                            except Exception as e:
                                print(f"Error getting full track data for {track['id']}: {e}")
                    
                    # Handle pagination if there are more tracks
                    while album_tracks['next']:
                        album_tracks = spotify.next(album_tracks)
                        for track in album_tracks['items']:
                            if track.get('id'):
                                try:
                                    full_track = spotify.track(track['id'])
                                    tracks.append(full_track)
                                except Exception as e:
                                    print(f"Error getting full track data for {track['id']}: {e}")
                    
                    print(f"Found {len(tracks)} tracks from album")
                    

                    # If we couldn't get enough tracks from the album, get artist's top tracks as well
                    if len(tracks) < 10 and album['artists']:
                        try:
                            artist_id = album['artists'][0]['id']
                            artist_top_tracks = spotify.artist_top_tracks(artist_id, country='US')
                            tracks.extend(artist_top_tracks['tracks'])
                            print(f"Added artist top tracks, now have {len(tracks)} tracks")
                        except Exception as e:
                            print(f"Error getting artist top tracks: {e}")
                
                except Exception as e:
                    print(f"Error getting album tracks: {e}")
                    tracks = []
                
                    artist_id = album['artists'][0]['id']
                    artist_top_tracks = spotify.artist_top_tracks(artist_id)
                    tracks.extend(artist_top_tracks['tracks'])
            
            else:
                raise ValueError(f"Invalid source type: {source_type}")
                
            # Limit to 20 tracks and remove duplicates
            track_ids_seen = set()
            unique_tracks = []
            for track in tracks:
                if track['id'] not in track_ids_seen and len(unique_tracks) < 20:
                    track_ids_seen.add(track['id'])
                    unique_tracks.append(track)
            
            tracks = unique_tracks
            
            if not tracks:
                raise ValueError(f"No tracks found for {source_type} {item_name}")
                
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404:
                raise ValueError(f"The {source_type} with ID '{item_id}' was not found on Spotify")
            else:
                raise ValueError(f"Spotify API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error getting tracks: {str(e)}")
            
        print(f"Successfully got {len(tracks)} tracks for {source_type} {item_name}")
        
        # Create a playlist from collected tracks
        playlist = spotify.user_playlist_create(
            user=user_id,
            name=name_prefix,
            public=False,
            description=f"Tracks {name_prefix}"
        )
        
        # Add tracks to playlist
        if tracks:
            track_uris = [track['uri'] for track in tracks]
            if track_uris:
                spotify.playlist_add_items(playlist['id'], track_uris)
        
        # Create ingredient from the playlist
        playlist_data = {
            "id": playlist['id'],
            "name": playlist['name'],
            "uri": playlist['uri'],
            "images": playlist.get('images', [])
        }
        
        ingredient_data = {
            'id': str(uuid.uuid4()),
            'job_id': str(job.id),
            'playlist': playlist_data,
            'quantity': 1  # Default quantity
        }
        
        # Create and add ingredient
        ingredient = Ingredient.from_dict(ingredient_data)
        job.recipe.append(ingredient)
        
        # Update job timestamp
        job.last_updated = int(time.time())
        
        # Save to database
        db.session.commit()
        
        # Return updated job
        return job.to_dict()
    
    def update_job(self, job_id, updated_job_data, user_id):
        print(f"Updating job {job_id} for user {user_id}")
        # ensure the user is in the db
        self.ensure_user_exists(user_id)
        # Try to find the existing job by job_id and user_id
        job = Job.query.filter_by(id=job_id, user_id=user_id).first()

        if job:
            # Update the existing job with new data
            for key, value in updated_job_data.items():
                if hasattr(job, key):
                    if key == 'recipe':
                        # Handle the 'recipe' separately since it's a relationship
                        job.recipe = []  # Clear existing ingredients

                        # Use a set to track playlist IDs for preventing duplicate ingredients
                        added_playlists = set()

                        for ingredient_data in value:
                            ingredient = Ingredient.from_dict(ingredient_data)
                            # Use the playlist id to determine uniqueness
                            playlist_id = ingredient.playlist.get('id')

                            if playlist_id not in added_playlists:
                                job.recipe.append(ingredient)
                                added_playlists.add(playlist_id)
                                # Update the last_updated timestamp
                                job.last_updated = int(time.time())
                            else:
                                print(
                                    f"Duplicate playlist detected: {playlist_id}, skipping.")
                    else:
                        # Update scalar attributes
                        setattr(job, key, value)
                else:
                    print(f"Server Job model does not have attribute: {key}")
        else:
            # Create a new job if it doesn't exist
            job = Job.from_dict(updated_job_data)
            job.id = job_id  # Assign the provided job_id
            job.user_id = user_id  # Ensure the job is linked to the correct user
            # Update the last_updated timestamp
            job.last_updated = int(time.time())
            db.session.add(job)

        db.session.commit()  # Commit the changes to the database
        return job.to_dict()  # Return the job as a dictionary

    def update_job_schedule(self, data):
        user_id = data['user_id']
        new_time = data['new_time']
        job_name = data.get('job_name', None)

        all_jobs = self.data_service.get_all_data()
        if user_id in all_jobs:
            for job in all_jobs[user_id]['jobs']:
                if job_name is None or job['name'] == job_name:
                    job['scheduled_time'] = new_time
            self.data_service.store_job_and_token(
                user_id, all_jobs[user_id]['jobs'], all_jobs[user_id]['token'])
            return jsonify({"status": "updated", "new_time": new_time})
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404
