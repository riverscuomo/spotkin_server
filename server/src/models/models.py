from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    playlist_id = db.Column(db.String, nullable=False)
    playlist_name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'playlist_name': self.playlist_name,
            'quantity': self.quantity
        }

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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    playlist_id = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    scheduled_time = db.Column(db.String, nullable=True)
    index = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    ban_skits = db.Column(db.Boolean, default=False)
    
    # Existing relationships
    recipe = db.relationship('Ingredient', backref='job', lazy=True, cascade="all, delete-orphan")
    
    # New relationships for other job components
    last_tracks = db.relationship('Track', secondary='job_last_tracks', backref='jobs_as_last')
    banned_artists = db.relationship('Artist', secondary='job_banned_artists', backref='jobs_banning')
    banned_tracks = db.relationship('Track', secondary='job_banned_tracks', backref='jobs_banning')
    banned_genres = db.relationship('Genre', secondary='job_banned_genres', backref='jobs_banning')
    exceptions_to_banned_genres = db.relationship('Artist', secondary='job_genre_exceptions', backref='jobs_excepting')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'playlist_id': self.playlist_id,
            'name': self.name,
            'scheduled_time': self.scheduled_time,
            'index': self.index,
            'description': self.description,
            'ban_skits': self.ban_skits,
            'recipe': [ingredient.to_dict() for ingredient in self.recipe],
            'last_tracks': [track.to_dict() for track in self.last_tracks],
            'banned_artists': [artist.to_dict() for artist in self.banned_artists],
            'banned_tracks': [track.to_dict() for track in self.banned_tracks],
            'banned_genres': [genre.name for genre in self.banned_genres],
            'exceptions_to_banned_genres': [artist.to_dict() for artist in self.exceptions_to_banned_genres],
        }


class Token(db.Model):
    __tablename__ = 'tokens'
    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    token_info = db.Column(db.JSON, nullable=False)
