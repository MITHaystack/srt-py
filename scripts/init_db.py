"""
Initializes the Users database table
"""
from sqlalchemy import Table, create_engine
from flask_sqlalchemy import SQLAlchemy
from srt.dashboard.messaging.user import User
from srt.dashboard.messaging.observation import Observation


# Connect to the database
engine = create_engine('sqlite:///data.sqlite')
conn = engine.connect()
db = SQLAlchemy()

Users_tbl = Table('user', User.metadata)
Obs_tbl = Table('observation', Observation.metadata)

def create_tables():
    User.metadata.create_all(engine)
    Observation.metadata.create_all(engine)

if __name__ == "__main__":
    create_tables()