"""user.py

Class Defining a User for Use With Flask-login
See https://flask-login.readthedocs.io/en/latest/

"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from ...dashboard import db


# db = SQLAlchemy()

class User(db.Model, UserMixin):
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    authenticated = db.Column(db.Boolean, default=False, nullable=False)
    validated = db.Column(db.Boolean, default=False, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    n_scheduled_observations = db.Column(db.Integer, default=0, nullable=False)
