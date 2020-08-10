"""app.py

Dash Small Radio Telescope Web App Dashboard

"""

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ClientsideFunction

import flask
import plotly.io as pio
import numpy as np
from time import time
from pathlib import Path

from .layouts import monitor_page, system_page
from .layouts.sidebar import generate_sidebar
from .messaging.status_fetcher import StatusThread
from .messaging.command_dispatcher import CommandThread
from .messaging.spectrum_fetcher import SpectrumThread


def generate_app(config_dir, config_dict):
    server = flask.Flask(__name__)
    app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
    )
    app.title = "SRT Dashboard"

    status_thread = StatusThread(port=5555)
    status_thread.start()

    command_thread = CommandThread(port=5556)
    command_thread.start()

    raw_spectrum_thread = SpectrumThread(port=5561)
    raw_spectrum_thread.start()

    cal_spectrum_thread = SpectrumThread(port=5563)
    cal_spectrum_thread.start()

    pages = {
        "Monitor Page": "monitor-page",
        "System Page": "system-page",
    }
    refresh_time = 3000  # ms

    pio.templates.default = "seaborn"
    side_title = "Small Radio Telescope"
    side_content = {
        "Status": dcc.Markdown(id="sidebar-status"),
        "Pages": html.Div(
            [
                html.H4("Pages"),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            page_name,
                            href=f"/{pages[page_name]}",
                            id=f"{pages[page_name]}-link",
                        )
                        for page_name in pages
                    ],
                    vertical=True,
                    pills=True,
                ),
            ]
        ),
    }
    sidebar = generate_sidebar(side_title, side_content)

    content = html.Div(id="page-content")
    layout = html.Div(
        [
            dcc.Location(id="url"),
            sidebar,
            content,
            dcc.Interval(id="interval-component", interval=refresh_time, n_intervals=0),
            html.Div(id="output-clientside"),
        ],
        id="mainContainer",
        style={
            "height": "100vh",
            "min_height": "100vh",
            "width": "100%",
            "display": "inline-block",
        },
    )

    app.layout = layout
    app.validation_layout = html.Div(
        [layout, monitor_page.generate_layout(), system_page.generate_layout(),]
    )
    # Create callbacks
    app.clientside_callback(
        ClientsideFunction(namespace="clientside", function_name="resize"),
        Output("output-clientside", "children"),
        [Input("page-content", "children")],
    )
    monitor_page.register_callbacks(
        app, status_thread, command_thread, raw_spectrum_thread, cal_spectrum_thread
    )
    system_page.register_callbacks(app, config_dict, status_thread)

    if config_dict["DASHBOARD_DOWNLOADS"]:
        @server.route("/download/<path:path>")
        def download(path):
            """Serve a file from the upload directory."""
            return flask.send_from_directory(
                Path(config_dict["SAVE_DIRECTORY"]).expanduser(), path, as_attachment=True
            )

    @app.callback(
        [Output(f"{pages[page_name]}-link", "active") for page_name in pages],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        if pathname == "/":
            # Treat page 1 as the homepage / index
            return tuple([i == 0 for i, _ in enumerate(pages)])
        return [pathname == f"/{pages[page_name]}" for page_name in pages]

    @app.callback(
        Output("sidebar", "className"),
        [Input("sidebar-toggle", "n_clicks")],
        [State("sidebar", "className")],
    )
    def toggle_classname(n, classname):
        if n and classname == "":
            return "collapsed"
        return ""

    @app.callback(
        Output("sidebar-status", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_status_display(n):
        status = status_thread.get_status()
        if status is None:
            # name = "Unknown"
            # lat = lon = np.nan
            az = el = np.nan
            az_offset = el_offset = np.nan
            cf = np.nan
            bandwidth = np.nan
            status_string = "SRT Not Connected"
        else:
            az = status["motor_azel"][0]
            el = status["motor_azel"][1]
            az_offset = status["motor_offsets"][0]
            el_offset = status["motor_offsets"][1]
            cf = status["center_frequency"]
            bandwidth = status["bandwidth"]
            time_dif = time() - status["time"]
            if time_dif > 5:
                status_string = "SRT Daemon Not Available"
            elif status["queue_size"] == 0 and status["queued_item"] == "None":
                status_string = "SRT Inactive"
            else:
                status_string = "SRT In Use!"

        status_string = f"""
         #### {status_string}
         - Motor Az, El: {az:.1f}, {el:.1f} deg
         - Motor Offsets: {az_offset:.1f}, {el_offset:.1f} deg
         - Center Frequency: {cf / pow(10, 6)} MHz
         - Bandwidth: {bandwidth / pow(10, 6)} MHz
        """
        return status_string

    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        if pathname in ["/", f"/{pages['Monitor Page']}"]:
            return monitor_page.generate_layout()
        elif pathname == f"/{pages['System Page']}":
            return system_page.generate_layout()
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )

    return server, app
