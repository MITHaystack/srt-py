"""user_data_handler.py

Class That Handles Reading and Writing User Data to a Database

"""

import sqlite3, werkzeug, os

class UserDatabase():

    """ Notes:
    .schema:
    
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_verified INTEGER DEFAULT 0,
        Is_admin INTEGER DEFAULT 0,
        n_sched_observations INTEGER DEFAULT 0
    );

    Can use werkzeug password hash function
    """

    def __init__(self):
        pass
    
    def open_database():
        pass

    """ Account Handling Functions """
    def register_user():
        pass

    def verify_user():
        pass

    def delete_user():
        pass

    def update_password_hash():
        pass

    def is_valid_login():
        pass

    """ Information getters (could also use @property decorator) """
    def get_email():
        pass

    def get_n_scheduled_observations():
        pass

    def get_all():
        pass

    


