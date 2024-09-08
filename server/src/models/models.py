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
        print('to_dict')
        print(self.playlist)
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
        print('Ingredient.from_dict')
        print(data)

        data.pop('id', None)
        data.pop('playlist_name', None)  # Ignore 'playlist_name'
        return cls(**data)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    last_updated = db.Column(db.Integer, default=int(time.time()))

    jobs = db.relationship('Job', backref='user',
                           lazy=True, cascade="all, delete-orphan")
    token = db.relationship('Token', uselist=False,
                            backref='user', cascade="all, delete-orphan")


class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    # playlist_id = db.Column(db.String, nullable=False)
    # Store full playlist as JSON
    target_playlist = db.Column(db.JSON, nullable=False)
    # playlist_name = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    scheduled_time = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    ban_skits = db.Column(db.Boolean, default=False)
    last_track_ids = db.Column(db.String, nullable=True)
    banned_artist_ids = db.Column(db.String, nullable=True)
    banned_track_ids = db.Column(db.String, nullable=True)
    banned_genres = db.Column(db.String, nullable=True)
    exceptions_to_banned_genres = db.Column(db.String, nullable=True)
    recipe = db.relationship('Ingredient', backref='job',
                             lazy=True, cascade="all, delete-orphan")
    min_popularity = db.Column(db.Integer, nullable=True)
    max_popularity = db.Column(db.Integer, nullable=True)
    min_duration = db.Column(db.Integer, nullable=True)
    max_duration = db.Column(db.Integer, nullable=True)
    min_danceability = db.Column(db.Integer, nullable=True)
    max_danceability = db.Column(db.Integer, nullable=True)
    min_energy = db.Column(db.Integer, nullable=True)
    max_energy = db.Column(db.Integer, nullable=True)
    min_acousticness = db.Column(db.Integer, nullable=True)
    max_acousticness = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': str(self.id),  # Convert UUID to string
            'user_id': self.user_id,
            # 'playlist_id': self.playlist_id,
            'target_playlist': self.target_playlist,
            # 'playlist_name': self.playlist_name,
            'name': self.name,
            'scheduled_time': self.scheduled_time,
            'description': self.description,
            'ban_skits': self.ban_skits,
            'last_track_ids': self.last_track_ids.split(',') if self.last_track_ids else [],
            'banned_artist_ids': self.banned_artist_ids.split(',') if self.banned_artist_ids else [],
            'banned_track_ids': self.banned_track_ids.split(',') if self.banned_track_ids else [],
            'banned_genres': self.banned_genres.split(',') if self.banned_genres else [],
            'exceptions_to_banned_genres': self.exceptions_to_banned_genres.split(',') if self.exceptions_to_banned_genres else [],
            'recipe': [ingredient.to_dict() for ingredient in self.recipe],
            'min_popularity': self.min_popularity,
            'max_popularity': self.max_popularity,
            'min_duration': self.min_duration,
            'max_duration': self.max_duration,
            'min_danceability': self.min_danceability,
            'max_danceability': self.max_danceability,
            'min_energy': self.min_energy,
            'max_energy': self.max_energy,
            'min_acousticness': self.min_acousticness,
            'max_acousticness': self.max_acousticness,
        }

    @classmethod
    def from_dict(cls, data):
        # Convert string lists back to comma-separated strings
        for field in ['last_track_ids', 'banned_artist_ids', 'banned_track_ids', 'banned_genres', 'exceptions_to_banned_genres']:
            if field in data and isinstance(data[field], list):
                data[field] = ','.join(data[field])

        # Remove 'id' from data if it exists, as it will be auto-generated
        data.pop('id', None)

        # Remove 'recipe' from data as it's a relationship and should be handled separately
        recipe_data = data.pop('recipe', [])

        # Create the Job instance
        job = cls(**data)

        # Handle the recipe relationship
        for ingredient_data in recipe_data:
            ingredient = Ingredient.from_dict(ingredient_data)
            job.recipe.append(ingredient)

        return job


class Token(db.Model):
    __tablename__ = 'tokens'
    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    token_info = db.Column(db.JSON, nullable=False)
