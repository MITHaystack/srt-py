"""
Initializes the Users database table
"""
import sqlite3, os
from sqlalchemy import Table, create_engine
from flask_sqlalchemy import SQLAlchemy
from srt.dashboard.messaging.user import Users

#connect to the database
conn = sqlite3.connect('../data.sqlite')
engine = create_engine('sqlite:///../../data.sqlite')
db = SQLAlchemy()

Users_tbl = Table('users', Users.metadata)

#fuction to create table using Users class
def create_users_table():
    Users.metadata.create_all(engine)

if __name__ == "__main__":
    create_users_table()