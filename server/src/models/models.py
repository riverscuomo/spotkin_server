from flask_sqlalchemy import SQLAlchemy
import time
from server.database.database import db


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
    
    # Store these as JSON or comma-separated strings
    last_track_ids = db.Column(db.String, nullable=True)  # or db.JSON
    banned_artist_ids = db.Column(db.String, nullable=True)  # or db.JSON
    banned_track_ids = db.Column(db.String, nullable=True)  # or db.JSON
    banned_genres = db.Column(db.String, nullable=True)  # or db.JSON
    exceptions_to_banned_genres = db.Column(db.String, nullable=True)  # or db.JSON

    recipe = db.relationship('Ingredient', backref='job', lazy=True, cascade="all, delete-orphan")

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
            'last_track_ids': self.last_track_ids.split(',') if self.last_track_ids else [],
            'banned_artist_ids': self.banned_artist_ids.split(',') if self.banned_artist_ids else [],
            'banned_track_ids': self.banned_track_ids.split(',') if self.banned_track_ids else [],
            'banned_genres': self.banned_genres.split(',') if self.banned_genres else [],
            'exceptions_to_banned_genres': self.exceptions_to_banned_genres.split(',') if self.exceptions_to_banned_genres else [],
        }
class Token(db.Model):
    __tablename__ = 'tokens'
    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    token_info = db.Column(db.JSON, nullable=False)
