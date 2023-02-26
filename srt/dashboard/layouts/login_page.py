"""monitor_page.py

Function for Generating Monitor Page and Creating Callback

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

from flask_login import login_user, logout_user, current_user

from pathlib import Path
from time import time
import base64
import io
from ..messaging.user import Users

def generate_layout():
    """Generates the Basic Layout for the Monitor Page

    Returns
    -------
    layout: html.div
        Monitor Page Layout
    """
    
    layout = html.Div(
        [
            # TODO
        ]
    )
    return layout


def register_callbacks(app, config):
    """Registers the Callbacks for the Login Page
    # TODO
    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    config : dict
        Contains All Settings for Dashboard / Daemon
    Returns
    -------
    None
    """

    # TODO

    @app.callback(Output("url", "pathname"), [Input("submit-button", "n_clicks")],
                [State("email-box", "em_value"), State("pw-box", "value")])
    def login_success(n, email_value, pw_value):
        # TODO
        """
        if n > 0:
            user = Users.query.filter_by(email=email_value).first()
            if user and check password hash
                login_user(user)
                return "/"
        else:
            pass
        """
        pass
    
    @app.callback(Output("status-div", "children"), [Input("submit-button", "n_clicks")],
                [State("email-box", "em_value"), State("pw-box", "value")])
    def login_fail(n, email_value, pw_value):
        # TODO
        """
        if n > 0:
            user = Users.query.filter_by(email=email_value).first()
            if not user:
                return "account not found"
            elif password hash invalid:
                return "invalid password"
        else:
            pass
        """
        pass

    # TODO Move to separate layout or navbar
    @app.callback(Output("url", "pathname"), [Input("logout-button", "n_clicks")])
    def logout(n):
        # TODO
        """
        if n > 0:
            logout user (current user)
        else:
            pass
        """
        pass