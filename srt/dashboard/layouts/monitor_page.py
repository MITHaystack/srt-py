import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output, State

import numpy as np
from astropy.time import Time
from scipy import signal
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
                                "SRT Monitoring Page",
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
                        [
                            html.Div(
                                [dcc.Graph(id="power-graph")],
                                className="pretty_container seven columns",
                            ),
                            html.Div(
                                [dcc.Markdown(id="status-display")],
                                style={},
                                className="pretty_container four columns",
                            ),
                        ],
                        className="row flex-display",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [dcc.Graph(id="spectrum-histogram")],
                                className="pretty_container twelve columns",
                            ),
                        ],
                    ),
                ]
            ),
        ]
    )
    return layout


def register_callbacks(app, status_thread, raw_spectrum_thread, cal_spectrum_thread):
    @app.callback(
        Output("spectrum-histogram", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_spectrum_histogram(n):
        max_precision = 2048
        spectrum = cal_spectrum_thread.get_spectrum()
        status = status_thread.get_status()
        if status is None or spectrum is None:
            return

        data = signal.resample(spectrum, max_precision)
        bandwidth = float(status["bandwidth"])
        cf = float(status["center_frequency"])
        data_range = np.linspace(-bandwidth / 2, bandwidth / 2, num=len(data)) + cf
        fig = go.Figure(
            layout={
                "title": "Spectrum",
                "height": 150,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        fig.add_trace(go.Scatter(x=data_range, y=data, name="Spectrum", mode="lines",))
        return fig

    @app.callback(
        Output("power-graph", "figure"), [Input("interval-component", "n_intervals")]
    )
    def update_power_graph(n):
        status = status_thread.get_status()
        if status is None:
            return
        tsys = float(status["temp_sys"])
        tcal = float(status["temp_cal"])
        cal_pwr = float(status["cal_power"])
        power_history = raw_spectrum_thread.get_power_history(tsys, tcal, cal_pwr)
        if power_history is None or len(power_history) == 0:
            return
        power_time, power_vals = zip(*power_history)
        fig = go.Figure(
            data=go.Scatter(x=[datetime.utcfromtimestamp(t) for t in power_time], y=power_vals),
            layout={
                "title": "Power vs Time",
                "height": 300,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        return fig

    @app.callback(
        Output("status-display", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_status_display(n):
        status = status_thread.get_status()
        if status is None:
            return ""

        name = status["location"]["name"]
        lat = status["location"]["latitude"]
        lon = status["location"]["longitude"]
        az = status["motor_azel"][0]
        el = status["motor_azel"][1]
        az_offset = status["motor_offsets"][0]
        el_offset = status["motor_offsets"][1]
        cf = status["center_frequency"]
        bandwidth = status["bandwidth"]
        status_string = f"""
        #### Current Status
         - Location: {name} ({lat}, {lon})
         - Motor Azimuth, Elevation: {az:.1f}, {el:.1f} deg
         - Motor Offsets: {az_offset}, {el_offset} deg
         - Time: {Time.now()}
         - Center Frequency: {cf / pow(10, 6)} MHz
         - Bandwidth: {bandwidth / pow(10, 6)} MHz
        """
        return status_string
