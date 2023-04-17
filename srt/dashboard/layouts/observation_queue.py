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

def generate_queue_list(user):
    
    if user:

        layout = html.Div([
            html.Ul([
                html.H3(f"User {user.name} has {user.n_scheduled_observations} observations scheduled"),
                html.Li("Observation 1: Some info"),
                html.Li("Observation 2: Some info"),
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

        


