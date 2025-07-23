import time
import uuid
from sqlalchemy.dialects.postgresql import UUID
from server.database.database import db
from sqlalchemy.dialects.postgresql import JSON


class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True),
                       db.ForeignKey('jobs.id'), nullable=False)
    # Store the entire playlist as JSON
    playlist = db.Column(JSON, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        # print('to_dict')
        # print(self.playlist)
        return {
            'id': str(self.id),
            'job_id': str(self.job_id),
            'playlist': self.playlist,  # Return the entire playlist object
            'quantity': self.quantity
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create an instance of the class from a dictionary.

        This class method takes a dictionary, removes the 'id' key if it exists,
        and uses the remaining key-value pairs to instantiate the class.

        Args:
            data (dict): A dictionary containing the attributes for the class instance.

        Returns:
            An instance of the class populated with the provided data.

        Examples:
            instance = MyClass.from_dict({'name': 'example', 'value': 42})
        """
        # print('Ingredient.from_dict')
        # print(data)

        data.pop('id', None)
        data.pop('playlist_name', None)  # Ignore 'playlist_name'
        return cls(**data)


class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    last_updated = db.Column(db.Integer, default=int(time.time()))
    last_autorun = db.Column(db.Integer, default=int(time.time()))
    created_at = db.Column(db.Integer, default=int(time.time()))
    target_playlist = db.Column(JSON, nullable=False)
    name = db.Column(db.String, nullable=False)
    scheduled_time = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    banned_artists = db.Column(JSON, nullable=True)
    banned_albums = db.Column(JSON, nullable=True)
    banned_tracks = db.Column(JSON, nullable=True)
    banned_genres = db.Column(JSON, nullable=True)
    ban_skits = db.Column(db.Boolean, default=False)
    banExplicitLyrics = db.Column(db.Boolean, default=False)
    exceptions_to_banned_genres = db.Column(JSON, nullable=True)
    last_tracks = db.Column(JSON, nullable=True)
    # Removed deprecated audio feature properties as they are no longer settable

    recipe = db.relationship('Ingredient', backref='job',
                             lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        print('Job.to_dict')
        
        # Calculate freeze status
        current_time = int(time.time())
        freeze_threshold = 1814400  # 21 days in seconds
        
        # Calculate time since last update
        time_since_update = None
        days_since_update = None
        is_frozen = False
        days_until_freeze = None
        
        if self.last_updated:
            # Handle milliseconds vs seconds
            if self.last_updated > 1e12:
                last_updated_seconds = self.last_updated / 1000
            else:
                last_updated_seconds = self.last_updated
                
            time_since_update = current_time - last_updated_seconds
            days_since_update = time_since_update / 86400  # Convert to days
            
            is_frozen = time_since_update > freeze_threshold
            if not is_frozen:
                days_until_freeze = (freeze_threshold - time_since_update) / 86400
        else:
            # Job without last_updated is considered frozen
            is_frozen = True
        
        return {
            'id': str(self.id),  # Convert UUID to string
            'user_id': self.user_id,
            'target_playlist': self.target_playlist,
            'name': self.name,
            'scheduled_time': self.scheduled_time,
            'description': self.description,
            'ban_skits': self.ban_skits,
            'banExplicitLyrics': self.banExplicitLyrics,
            'last_tracks': self.last_tracks or [],
            'exceptions_to_banned_genres': self.exceptions_to_banned_genres or [],
            'recipe': [ingredient.to_dict() for ingredient in self.recipe],
            # Removed deprecated audio feature properties
            'banned_artists': self.banned_artists or [],
            'banned_albums': self.banned_albums or [],
            'banned_tracks': self.banned_tracks or [],
            'banned_genres': self.banned_genres or [],
            # New freeze status fields
            'last_updated': self.last_updated,
            'freeze_status': {
                'is_frozen': is_frozen,
                'days_since_update': round(days_since_update, 1) if days_since_update is not None else None,
                'days_until_freeze': round(days_until_freeze, 1) if days_until_freeze is not None else None,
                'freeze_threshold_days': 21
            }
        }

    @classmethod
    def from_dict(cls, data):
        print('Job.from_dict')

        # No need to convert lists to strings, as these are JSON fields
        recipe_data = data.pop('recipe', [])
        job = cls(**data)

        name = data.get('target_playlist', {}).get('name') or 'New Spotkin'
        job.name = name

        for ingredient_data in recipe_data:
            ingredient = Ingredient.from_dict(ingredient_data)
            job.recipe.append(ingredient)

        return job


class Token(db.Model):
    __tablename__ = 'tokens'
    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    token_info = db.Column(db.JSON, nullable=False)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    last_updated = db.Column(db.Integer, default=int(time.time()))
    created_at = db.Column(db.Integer, default=int(time.time()))

    jobs = db.relationship('Job', backref='user',
                           lazy=True, cascade="all, delete-orphan")
    token = db.relationship('Token', uselist=False,
                            backref='user', cascade="all, delete-orphan")
