import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from datetime import datetime


def generate_layout():
    layout = html.Div(
        [
            html.Div(
                [
                    html.Div([], className="one-third column",),
                    html.Div(
                        [
                            html.H3(
                                "SRT System Page",
                                style={"margin-bottom": "0px", "text-align": "center"},
                            ),
                        ],
                        className="one-third column",
                        id="title",
                    ),
                    html.Div([], className="one-third column", id="button"),
                ],
                id="header",
                className="row flex-display",
                style={"margin-bottom": "25px"},
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Markdown(id="emergency-contact-info")],
                        className="pretty_container three columns",
                    ),
                    html.Div(
                        [
                            html.H4(
                                "Message Logs",
                                style={"margin-bottom": "0px", "text-align": "center"},
                            ),
                            html.Div(
                                id="message-logs",
                                style={
                                    "height": 200,
                                    "overflow": "hidden",
                                    "overflow-y": "scroll",
                                },
                            ),
                        ],
                        className="pretty_container eight columns",
                    )
                ],
                className="row flex-display",
            ),
        ]
    )
    return layout


def register_callbacks(app, status_thread, command_thread):
    @app.callback(
        Output("emergency-contact-info", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_contact_info(n):
        status = status_thread.get_status()
        if status is None or "emergency_contact" not in status:
            return ""
        status = status["emergency_contact"]
        status_string = f"""
        ##### Emergency Contact Info
         - Name: {status["name"]}
         - Email: {status["email"]}
         - Phone Number: {status["phone_number"]}
        """
        return status_string

    @app.callback(
        Output("message-logs", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_message_logs(n):
        status = status_thread.get_status()
        if status is None or "error_logs" not in status:
            return ""
        status = status["error_logs"]
        children = [
            html.P(
                f"{datetime.fromtimestamp(log_time).strftime('%Y-%m-%d %H:%M:%S')}: {log_txt}"
            )
            for log_time, log_txt in status
        ]
        return html.Div(children=children)
