import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from .navbar import generate_navbar


def generate_layout():
    layout = html.Div(
        [
            # generate_navbar(buttons),
            html.Div(
                [
                    html.Button("Stow", id="btn-stow", n_clicks=0),
                    html.Button("AzEl", id="btn-point-azel", n_clicks=0),
                    html.Button("Set Freq", id="btn-set-freq", n_clicks=0),
                    html.Button("Set Offsets", id="btn-set-offset", n_clicks=0),
                    html.Button("Record", id="btn-record", n_clicks=0),
                ],
                className="row flex-dispaly"
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="az-el-graph")],
                        className="pretty_container twelve columns",
                    ),
                ],
                className="row flex-display",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Header"),
                    dbc.ModalBody("This is the content of the modal"),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="ml-auto")
                    ),
                ],
                id="modal",
            ),
            html.Div(id="signal", style={"display": "none"}),
        ]
    )
    return layout


def register_callbacks(app, command_thread):

    @app.callback(
        Output("modal", "is_open"),
        [Input("az-el-graph", "clickData"), Input("close", "n_clicks")],
        [State("modal", "is_open")],
    )
    def display_click_data(clickData, n_clicks, is_open):
        print(clickData, end=" ")  # TODO: Remove
        print(n_clicks, end=" ")  # TODO: Remove
        print(is_open)  # TODO: Remove
        if n_clicks or clickData:
            return not is_open
        return is_open

    @app.callback(
        Output("signal", "children"),
        [Input("btn-stow", "n_clicks")]
    )
    def stow(n_clicks):
        if n_clicks:
            command_thread.add_to_queue("stow")
