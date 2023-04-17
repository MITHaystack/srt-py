"""observation.py

Class Defining an Observation Table
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from .user import User
from ...dashboard import db


# db = SQLAlchemy()

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

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref=db.backref('observations', lazy=True))

    @classmethod
    def from_dict(self, config):
        target_name = config.get("target_obj_name")
        file_name = config.get("output_file_name")
        try:
            name = config["obs_name"]
            schd_time = config["scheduled_time"]
            strt_time = config["obs_start_time"]
            ra = config["ra"]
            dec = config["dec"]
            duration = config["duration"]
        except KeyError as ke:
            raise KeyError("Error: Missing required field(s):\n" + repr(ke))

        if not file_name:
            file_name = name + str(schd_time).replace(' ', "_")

        return Observation(
            obs_name = name,
            target_obj_name=target_name,
            scheduled_time=schd_time,
            start_time=strt_time,
            ra=ra,
            dec=dec,
            duration=duration,
            output_file_name=file_name
        )
            
    def __repr__(self) -> str:
        return f"""<Observation '{self.obs_name}'>"""
    
