import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

from .graphs import generate_az_el_graph

import numpy as np
from astropy.time import Time


def generate_layout():
    layout = html.Div([
        html.Div([
            dcc.Graph(
                id='az-el-graph'
            ),
            dcc.Graph(
                id='spectrum-histogram'
            ),
            dcc.Graph(
                id='power-graph'
            ),
            dcc.Markdown(
                id='status-display'
            )
        ]),
        dbc.Modal(
            [
                dbc.ModalHeader("Header"),
                dbc.ModalBody("This is the content of the modal"),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
        )
    ])
    return layout


def register_callbacks(app):
    # Multiple components can update everytime interval gets fired.
    @app.callback(Output('az-el-graph', 'figure'),
                  [Input('interval-component', 'n_intervals')])
    def update_az_el_graph(n):
        return generate_az_el_graph((270, 90), (30, 60))

    @app.callback(Output('spectrum-histogram', 'figure'),
                  [Input('interval-component', 'n_intervals')])
    def update_spectrum_histogram(n):
        x = np.random.randn(500)
        fig = go.Figure(data=[go.Histogram(x=x)])
        return fig

    @app.callback(Output('power-graph', 'figure'),
                  [Input('interval-component', 'n_intervals')])
    def update_power_graph(n):
        x = np.arange(10)
        fig = go.Figure(data=go.Scatter(x=x, y=x ** 2))
        return fig

    @app.callback(Output('status-display', 'children'),
                  [Input('interval-component', 'n_intervals')])
    def update_status_display(n):
        name = "Haystack"
        lat = 42.5
        lon = -71
        az = 80
        el = 45
        az_offset = 0
        el_offset = 0
        cf = 1420
        bandwidth = 2
        status_string = f"""
        ## Current Status
         - Location: {name} (lat: {lat}, lon {lon})
         - Motor Azimuth, Elevation: {az}, {el} deg
         - Motor Offsets: {az_offset}, {el_offset} deg
         - Time: {Time.now()}
         - Center Frequency: {cf} MHz
         - Bandwidth: {bandwidth} MHz
        """
        return status_string

    @app.callback(
        Output("modal", "is_open"),
        [Input('az-el-graph', 'clickData'), Input("close", "n_clicks")],
        [State("modal", "is_open")])
    def display_click_data(clickData, n_clicks, is_open):
        print(clickData, end=" ")  # TODO: Remove
        print(n_clicks, end=" ")  # TODO: Remove
        print(is_open)  # TODO: Remove
        if n_clicks or clickData:
            return not is_open
        return is_open
