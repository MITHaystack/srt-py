"""
Initializes the Users database table
"""
from sqlalchemy import Table, create_engine
from flask_sqlalchemy import SQLAlchemy
from srt.dashboard.messaging.user import User


# Connect to the database
engine = create_engine('sqlite:///data.sqlite')
conn = engine.connect()
db = SQLAlchemy()

Users_tbl = Table('user', User.metadata)

def create_tables():
    User.metadata.create_all(engine)

if __name__ == "__main__":
    create_tables()