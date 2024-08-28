# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    # If you need to use the engine directly
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine))

    return db_session
