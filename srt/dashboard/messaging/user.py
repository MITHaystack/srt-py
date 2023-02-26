"""user.py

Class Defining a User for Use With Flask-login
See https://flask-login.readthedocs.io/en/latest/

"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, create_engine
import sqlite3

db = SQLAlchemy()

class Users(db.Model):
    """
    Need:
    insert into database
    check if user exists
    """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    authenticated = db.Column(db.Boolean, default=False, nullable=False)
    validated = db.Column(db.Boolean, default=False, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    n_scheduled_observations = db.Column(db.Integer, default=0, nullable=False)

    
    @property
    def is_authenticated(self) -> bool:
        """ 
        returns: True if user is authenticated, else False
        """
        return self.authenticated

    @property
    def is_active(self) -> bool:
        """ 
        returns: True if user has validated email, else False
        """
        # TODO
        # return self.validated
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """ 
        returns: True if user is anonymous, else False
        """
        # TODO
        return False

    def get_id(self) -> str:
        """ 
        returns: str containing the user's ID
        """
        return str(self.id)