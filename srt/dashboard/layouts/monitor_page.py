"""monitor_page.py

Function for Generating Monitor Page and Creating Callback

"""

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import numpy as np
from datetime import datetime


def generate_layout():
    """Generates the Basic Layout for the Monitor Page

    Returns
    -------
    Monitor Page Layout
    """
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
                                [],
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
    """Registers the Callbacks for the Monitor Page

    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    status_thread : Thread
        Thread for Getting Status from Daemon
    raw_spectrum_thread : Thread
        Thread for Getting Raw Spectrum Data from Daemon
    cal_spectrum_thread : Thread
        Thread for Getting Calibrated Spectrum Data from Daemon

    Returns
    -------
    None
    """
    @app.callback(
        Output("spectrum-histogram", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_spectrum_histogram(n):
        spectrum = cal_spectrum_thread.get_spectrum()
        status = status_thread.get_status()
        if status is None or spectrum is None:
            return ""
        bandwidth = float(status["bandwidth"])
        cf = float(status["center_frequency"])
        data_range = np.linspace(-bandwidth / 2, bandwidth / 2, num=len(spectrum)) + cf
        fig = go.Figure(
            layout={
                "title": "Spectrum",
                "xaxis_title": "Frequency (Hz)",
                "yaxis_title": "Temperature (K)",
                "height": 150,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        fig.add_trace(go.Scatter(x=data_range, y=spectrum, name="Spectrum", mode="lines",))
        return fig

    @app.callback(
        Output("power-graph", "figure"), [Input("interval-component", "n_intervals")]
    )
    def update_power_graph(n):
        status = status_thread.get_status()
        if status is None:
            return ""
        tsys = float(status["temp_sys"])
        tcal = float(status["temp_cal"])
        cal_pwr = float(status["cal_power"])
        spectrum_history = raw_spectrum_thread.get_history()
        if spectrum_history is None:
            return ""
        power_history = []
        for t, spectrum in spectrum_history:
            p = np.sum(spectrum)
            a = len(spectrum)
            pwr = (tsys + tcal) * p / (a * cal_pwr)
            power_history.insert(0, (t, pwr))
        if power_history is None or len(power_history) == 0:
            return ""
        power_time, power_vals = zip(*power_history)
        fig = go.Figure(
            data=go.Scatter(x=[datetime.utcfromtimestamp(t) for t in power_time], y=power_vals),
            layout={
                "title": "Power vs Time",
                "xaxis_title": "Timestamp",
                "yaxis_title": "Calibrated Power",
                "height": 300,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        return fig
