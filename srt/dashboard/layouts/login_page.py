"""login_page.py

Functions for Generating Login Page Layout and Creating Callbacks

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
from pathlib import Path
import base64

from flask_login import login_user

from ..messaging.user import User
from werkzeug.security import check_password_hash


def generate_layout() -> html.Div:
    """Generates the Basic Layout for the Login Page

    Returns
    -------
    layout: html.div
        Login Page Layout
    """
    curfold = Path(__file__).parent.absolute()
    bg_fname = curfold.parent.joinpath(
        "images", "landing_bg.png"
    )
    logo_fname = curfold.parent.joinpath(
        "images", "landing_logos.png"
    )
    bg_encoded = base64.b64encode(open(bg_fname, "rb").read())
    logo_encoded = base64.b64encode(open(logo_fname, "rb").read())
    img_style = {
        "display": "block",
        "min-width": "100%",
        "height": "100%",
        "object-fit": "cover"
    }
    img_div_style = {
        "width": "50%",
        "height": "100vh",
        "overflow": "hidden"
    }
    right_style = {
        "width": "50%",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "flex-direction": "column"
    }
    logo_style = {
        "display": "block",
        "max-width": "80%",
        "position": "relative",
        "bottom": 220,
        "left": 15
    }
    container_style = {
        "display": "flex",
        "width": "100%"
    }


    layout = html.Div([dcc.Location(id="url_login", refresh=True),
                html.Div(id="hidden_for_redirect"),
                html.Div(id="container", children=[
                    html.Div([
                        html.Img(src="data:image/png;base64,{}".format(
                                            bg_encoded.decode()
                                        ),
                                style=img_style),
                        html.Img(src="data:image/png;base64,{}".format(
                                            logo_encoded.decode()
                                        ),
                                style=logo_style),
                    ], id="img-div", style=img_div_style),
                    html.Div([
                        html.H2("Tufts Radio Telescope"),
                        dcc.Input(placeholder="Email",
                            type="text",
                            id="email-box"),
                        dcc.Input(placeholder="Password",
                            type="password",
                            id="pw-box"),
                        html.Button(children="Launch",
                            n_clicks=0,
                            type="submit",
                            id="login-button"),
                        html.Div(id="status-div"),
                        html.Div([html.P("New?"), 
                                dcc.Link("Create Account", 
                                            href="/create")])
                    ], style=right_style)
                    ], style=container_style)
                ])

    return layout

def register_callbacks(app) -> None:
    """Registers the Callbacks for the Login Page
    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    Returns
    -------
    None
    """

    @app.callback(Output("hidden_for_redirect", "children"), [Input("login-button", "n_clicks")],
    [State("email-box", "value"), State("pw-box", "value")])
    def login_valid(n_clicks: int, email_value: str, pw_value: str):
        """Checks for valid info, logs user in, redirects to monitor page
        Parameters
        ----------
        n: int - number of clicks on login-button
        email_value: str - value of email input field
        pw_value: str - value of password input field
        
        Returns
        -------
        List of Dash Components
        """
        if n_clicks > 0:
            user = User.query.filter_by(email=email_value).first()
            if user and check_password_hash(user.password, pw_value):
                # TODO check if "remember me box is checked"
                login_user(user)
                return [dcc.Location(pathname="/", id="hi", refresh=True)]
        else:
            raise PreventUpdate()
        
    
    @app.callback(Output("status-div", "children"), [Input("login-button", "n_clicks")],
                [State("email-box", "value"), State("pw-box", "value")])
    def login_invalig(n_clicks: int, email_value: str, pw_value: str):
        """Checks for invalid info, updates div with error message
        Parameters
        ----------
        n : int - number of clicks on login-button
        email_value: str - value of email input field
        pw_value: str - value of password input field
        
        Returns
        -------
        List of Dash Components
        """
        if n_clicks > 0:
            user = User.query.filter_by(email=email_value).first()
            if not user:
                return ["Account not found"]
            elif not check_password_hash(user.password, pw_value):
                return ["Incorrect password"]
            else:
                raise PreventUpdate()
        else:
            raise PreventUpdate()
       

    # # TODO Move to separate layout or navbar
    # @app.callback(Output("url", "pathname"), [Input("logout-button", "n_clicks")])
    # def logout(n):
    #     # TODO
    #     """
    #     if n > 0:
    #         logout user (current user)
    #     else:
    #         pass
    #     """
    #     pass