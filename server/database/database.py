# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()

def init_db(app):
    # This is important: make the db instance available at the module level
    global db
    db.init_app(app)

    # If you need to use the engine directly
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine))

    
    db = SQLAlchemy(app)

    return db  # Return the db instance instead of db_session
