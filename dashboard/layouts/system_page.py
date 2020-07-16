import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State


def generate_layout():
    layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Markdown(id="emergency-contact-info")
                        ],
                        className="mini_container"
                    )
                ],
                className="row flex-display",
            )
        ]
    )
    return layout


def register_callbacks(app, status_thread, command_thread):
    @app.callback(
        Output("emergency-contact-info", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_contact_info(n):
        status = status_thread.get_status()["emergency_contact"]
        if status is None:
            return ""
        status_string = f"""
        ##### Emergency Contact Info
         - Name: {status["name"]}
         - Email: {status["email"]}
         - Phone Number: {status["phone_number"]}
        """
        return status_string
