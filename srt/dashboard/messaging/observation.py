"""observation.py

Class Defining an Observation Table
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Observation(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    obs_name = db.Column(db.String, nullable=False)
    target_obj_name = db.Column(db.String)

    # The time when the observation was created (scheduled) and when it will be run
    scheduled_time = db.Column(db.DateTime, nullable=False)
    obs_start_time = db.Column(db.DateTime, nullable=False)

    # Specify Celestial coordinates as CSV
    # e.g. ra="05,31,30"
    ra = db.Column(db.String, nullable=False)
    dec = db.Column(db.String, nullable=False)

    # Recording duration in seconds
    duration = db.Column(db.Integer, nullable=False)

    output_file_name = db.Column(db.String, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship('User', backref=db.backref('observations', lazy=True))



    