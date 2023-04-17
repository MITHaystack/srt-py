"""create_page.py

Functions for Generating Create Page Layout and Creating Callbacks

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

from flask_login import login_user

from ..messaging.user import User
from werkzeug.security import generate_password_hash


def generate_layout() -> html.Div:
    """Generates the Basic Layout for the Monitor Page

    Returns
    -------
    layout: html.div
        Create Page Layout
    """
    
    layout = html.Div([dcc.Location(id="url_create", refresh=True),
            html.Div(id="hidden_for_redirect_create"),
            html.H1("Create User Account"),
            dcc.Location(id="create_user", refresh=True),
            dcc.Input(id="name",
                      type="text",
                      placeholder="name",
                      maxLength =15),
            dcc.Input(id="email",
                      type="email",
                      placeholder="email",
                      maxLength = 50),
            dcc.Input(id="password",
                      type="password",
                      placeholder="password"),
            html.Button("Create User", id="create-button", n_clicks=0),
            html.Div(id="container-button-basic"),
            html.Div([html.H2("Already have a user account?"), 
                      dcc.Link("Click here to Log In", href="/login")])])
    return layout


def register_callbacks(app, db) -> None:
    """Registers the Callbacks for the Create Account Page
    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    db: Flask-SQLAlchemy database Object for user data handling    
    Returns
    -------
    None
    """

    # TODO remove "account not found" when re-entering information

    @app.callback(
    [Output("hidden_for_redirect_create", "children")]
    , [Input("create-button", "n_clicks")]
    , [State("name", "value"), State("email", "value"), State("password", "value")])
    def insert_users_valid(n_clicks: int, name: str, em: str, pw: str):
        """Creates a new user account, inserting into database
        Parameters
        ----------
        n: int - number of clicks of create-button
        name: str - user"s name
        em: str - user"s email
        pw: str - user"s unhashed password
        Returns
        -------
        List of Dash Components
        """
        if n_clicks > 0:
            if name is not None and pw is not None and em is not None:
                hashed_password = generate_password_hash(pw, method="sha256")
                
                new = User(
                    name=name, email=em, password=hashed_password,
                    authenticated=False, validated=False, admin=False,
                    n_scheduled_observations=0)
                db.session.add(new)
                db.session.commit()
                login_user(new)
                return [dcc.Location(pathname="/", id="hi2", refresh=True)]
            else:
                return ["Please fill out all fields"]
        else:
            raise PreventUpdate()

    # TODO
    # @app.callback(
    # [Output("container-button-basic", "children")]
    # , [Input("create-button", "n_clicks")]
    # , [State("name", "value"), State("email", "value"), State("password", "value")])
    # # , State("create-button", "n-clicks")])
    # def insert_users_invalid(n: int, name: str, em: str, pw: str):
    #     return [""]
