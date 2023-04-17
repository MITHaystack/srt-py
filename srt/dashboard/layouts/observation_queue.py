"""observation_queue.py

Generate a list component showing any queued observations for the current user

"""

import dash

try:
    from dash import dcc
except:
    import dash_core_components as dcc

import dash_bootstrap_components as dbc

try:
    from dash import html
except:
    import dash_html_components as html

from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

from datetime import datetime

from ..messaging.user import User
from ..messaging.observation import Observation

from ...dashboard import db


def commit_observation(config: dict, user: User) -> None:
    """Create a new observation for a user and add it to the database

    Parameters
    ----------
    config : dict - observations settings. See observation.py
    user: Flask-login user proxy

    Returns
    -------
    None
    """

    obs = Observation.from_dict(config)
    obs.user = user
    user.n_scheduled_observations += 1
    db.session.commit()


def generate_queue_list(user):
    
    if user:

        layout = html.Div([
            html.H3(f"User {user.name} has {user.n_scheduled_observations} observations scheduled"),
            html.Ul([
                html.Li(f"Observation: {obs.obs_name}")
                for obs in user.observations
            ]),
            dcc.Input(placeholder="Observation Name",
                      type="text",
                      id="obs-name"),
            html.Button("Create New Observation", id="new-obs-button", n_clicks=0),
            html.Div(id="obs-status")
        ])
        return layout
    else:
        return ""

def register_obs_callbacks(app, user) -> None:
    """Registers the Callbacks for the Observation Queue

    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    user: Flask-login user proxy

    Returns
    -------
    None
        """
    
    @app.callback(Output("obs-status", "children"),
                  Input("new-obs-button", "n_clicks"),
                  [State("obs-name", "value")])
    def schedule_and_update_output(n: int, name: str) -> html.Div:
        """Registers the Callbacks for the Observation Queue

        Parameters
        ----------
        n : int - number of clicks on button
        name: str - name of the observation
        Returns
        -------
        None
        """
        if n > 0:
            if not name:
                return [""]
            if user.is_authenticated:
                obs = Observation(obs_name=name,
                                scheduled_time=datetime.now(),
                                obs_start_time=datetime.now(),
                                ra="05,31,30", dec="05,31,30",
                                duration=600,
                                output_file_name="hello.fits",
                                user=user)
                user.n_scheduled_observations += 1
                db.session.commit()
                return html.Div(html.H4(f"Observation {name} successfully scheduled for user {user.name}, now has {user.n_scheduled_observations} scheduled"))
        else:
            raise PreventUpdate()
    
        


