from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()


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


class Token(db.Model):
    __tablename__ = 'tokens'
    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    token_info = db.Column(db.JSON, nullable=False)
