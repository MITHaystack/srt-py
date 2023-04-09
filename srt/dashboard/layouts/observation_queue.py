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

from ..messaging.user import User

def generate_queue_list(user):
    
    if user:

        layout = html.Div([
            html.Ul([
                html.H3(f"User {user.name} has {user.n_scheduled_observations} observations scheduled"),
                html.Li("Observation 1: Some info"),
                html.Li("Observation 2: Some info"),
            ])
        ])
        return layout
    else:
        return ""