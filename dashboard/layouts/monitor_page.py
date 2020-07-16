import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import numpy as np
from astropy.time import Time


def generate_layout():
    layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                        ],
                        className="one-third column",
                    ),
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
                    html.Div(
                        [
                        ],
                        className="one-third column",
                        id="button"
                    ),
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
                                [
                                    html.Div(
                                        [dcc.Graph(id="spectrum-histogram-a"),],
                                        className="mini_container",
                                    ),
                                    html.Div(
                                        [dcc.Graph(id="spectrum-histogram-b"),],
                                        className="mini_container",
                                    ),
                                    html.Div(
                                        [dcc.Graph(id="spectrum-histogram-c")],
                                        className="mini_container",
                                    ),
                                ],
                                className="three columns",
                            ),
                            html.Div(
                                [dcc.Markdown(id="status-display")],
                                style={},
                                className="pretty_container two columns",
                            ),
                        ],
                        className="row flex-display",
                    ),
                    # html.Div(
                    #     [
                    #         html.Div(
                    #             [dcc.Graph(id="az-el-graph")],
                    #             className="pretty_container twelve columns",
                    #         ),
                    #     ],
                    #     className="row flex-display",
                    # ),
                ]
            ),
        ]
    )
    return layout


def register_callbacks(app, status_thread):
    # @app.callback(
    #     Out
    #     [Input("interval-component", "n_intervals")]
    # )

    @app.callback(
        Output("spectrum-histogram-a", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_spectrum_histogram_a(n):
        x = np.random.randn(500)
        fig = go.Figure(
            data=[go.Histogram(x=x)],
            layout={
                "title": "Spectrum",
                "height": 150,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        return fig

    @app.callback(
        Output("spectrum-histogram-b", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_spectrum_histogram_b(n):
        x = np.random.randn(500)
        fig = go.Figure(
            data=[go.Histogram(x=x)],
            layout={
                "title": "Spectrum",
                "height": 150,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        return fig

    @app.callback(
        Output("spectrum-histogram-c", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_spectrum_histogram_c(n):
        x = np.random.randn(500)
        fig = go.Figure(
            data=[go.Histogram(x=x)],
            layout={
                "title": "Spectrum",
                "height": 150,
                "margin": dict(l=20, r=20, b=20, t=30, pad=4,),
            },
        )
        return fig

    @app.callback(
        Output("power-graph", "figure"), [Input("interval-component", "n_intervals")]
    )
    def update_power_graph(n):
        x = np.arange(10)
        fig = go.Figure(
            data=go.Scatter(x=x, y=x ** 2),
            layout={
                "title": "Power vs Time",
                "height": 500,
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
         - Motor Azimuth, Elevation: {az}, {el} deg
         - Motor Offsets: {az_offset}, {el_offset} deg
         - Time: {Time.now()}
         - Center Frequency: {cf / pow(10, 6)} MHz
         - Bandwidth: {bandwidth / pow(10, 6)} MHz
        """
        return status_string
