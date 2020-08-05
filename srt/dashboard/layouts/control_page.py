"""control_page.py

Function for Generating Control Page and Creating Callback

"""

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import base64
import io

from .navbar import generate_navbar
from .graphs import generate_az_el_graph


def generate_layout():
    """Generates the Basic Layout for the Control Page

    Returns
    -------
    Control Page Layout
    """
    drop_down_buttons = {
        "Antenna": [
            dbc.DropdownMenuItem("Stow", id="btn-stow"),
            dbc.DropdownMenuItem("Set AzEl", id="btn-point-azel"),
            dbc.DropdownMenuItem("Set Offsets", id="btn-set-offset"),
        ],
        "Radio": [
            dbc.DropdownMenuItem("Set Frequency", id="btn-set-freq"),
            dbc.DropdownMenuItem("Set Bandwidth", id="btn-set-samp"),
        ],
        "Routine": [
            dbc.DropdownMenuItem("Start Recording", id="btn-start-record"),
            dbc.DropdownMenuItem("Stop Recording", id="btn-stop-record"),
            dbc.DropdownMenuItem("Calibrate", id="btn-calibrate"),
        ],
        "Power": [dbc.DropdownMenuItem("Shutdown", id="btn-quit")],
    }
    layout = html.Div(
        [
            html.Div(
                [
                    html.Div([], className="one-third column",),
                    html.Div(
                        [
                            html.H3(
                                "SRT Control Page",
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
            generate_navbar(drop_down_buttons),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4(
                                id="text-queue-status", style={"text-align": "center"}
                            ),
                            dcc.Markdown(id="command-display"),
                        ],
                        className="pretty_container five columns",
                    ),
                    html.Div(
                        [
                            html.H4("Upload Command File"),
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(
                                    ["Drag and Drop or ", html.A("Select Files")]
                                ),
                                style={
                                    "width": "95%",
                                    "hSystemeight": "60px",
                                    "lineHeight": "60px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "margin": "10px",
                                },
                                # Allow multiple files to be uploaded
                                multiple=False,
                            ),
                            html.Div(
                                id="output-data-upload", style={"text-align": "center"}
                            ),
                        ],
                        className="pretty_container six columns",
                    ),
                ],
                className="row flex-display",
                style={"display": "flex", "justify-content": "center"},
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
                    dbc.ModalHeader("Point at Object"),
                    dbc.ModalBody(
                        [
                            html.H5("Confirm Pointing to This Object?"),
                            dcc.RadioItems(
                                options=[
                                    {"label": "Direct Point", "value": ""},
                                    {"label": "N-Point Scan", "value": " n"},
                                    {"label": "Beam-switch", "value": " b"},
                                ],
                                id="point-options",
                                value="",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="az-el-graph-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="az-el-graph-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="az-el-graph-modal",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Enter Azimuth and Elevation"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="azimuth",
                                type="number",
                                debounce=True,
                                placeholder="Azimuth",
                            ),
                            dcc.Input(
                                id="elevation",
                                type="number",
                                debounce=True,
                                placeholder="Elevation",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="point-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="point-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="point-modal",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Enter the New Center Frequency"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="frequency",
                                type="number",
                                debounce=True,
                                placeholder="Center Frequency (MHz)",
                                style={"width": "100%"},
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="freq-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="freq-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="freq-modal",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Enter the New Sample Frequency"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="samples",
                                type="number",
                                debounce=True,
                                placeholder="Sample Frequency (MHz)",
                                style={"width": "100%"},
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="samp-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="samp-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="samp-modal",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Enter the Motor Offsets"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="offset-azimuth",
                                type="number",
                                debounce=True,
                                placeholder="Azimuth Offset (deg)",
                            ),
                            dcc.Input(
                                id="offset-elevation",
                                type="number",
                                debounce=True,
                                placeholder="Elevation Offset (deg)",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="offset-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="offset-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="offset-modal",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Start Recording"),
                    dbc.ModalBody(
                        [
                            html.H5("Select a File Type"),
                            dcc.RadioItems(
                                options=[
                                    {"label": "Digital RF (Raw Data)", "value": ""},
                                    {
                                        "label": ".rad Format (Spectrum)",
                                        "value": " *.rad",
                                    },
                                    {
                                        "label": ".fits Format (Spectrum)",
                                        "value": "*.fits",
                                    },
                                ],
                                id="record-options",
                                value="",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="record-btn-yes",
                                className="ml-auto",
                                block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="record-btn-no",
                                className="ml-auto",
                                block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="record-modal",
            ),
            html.Div(id="signal", style={"display": "none"}),
        ]
    )
    return layout


def register_callbacks(app, status_thread, command_thread):
    """Registers the Callbacks for the Control Page

    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    status_thread : Thread
        Thread for Getting Status from Daemon
    command_thread : Thread
        Thread for Sending Commands to Daemon

    Returns
    -------
    None
    """

    @app.callback(
        Output("output-data-upload", "children"),
        [Input("upload-data", "contents")],
        [State("upload-data", "filename"), State("upload-data", "last_modified")],
    )
    def update_output(contents, name, date):
        if contents is not None:
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            try:
                if "txt" in name or "cmd" in name:
                    # Assume that the user uploaded a txt file
                    loaded_file = io.StringIO(decoded.decode("utf-8"))
                    lines = [line.rstrip() for line in loaded_file]
                    for line in lines:
                        command_thread.add_to_queue(line)
                    return html.Div(["Command File Uploaded Successfully"])
            except Exception as e:
                print(e)
            return html.Div(["There was an error processing this file."])
        else:
            return html.Div(["Awaiting Command File"])

    @app.callback(
        Output("az-el-graph", "figure"), [Input("interval-component", "n_intervals")]
    )
    def update_az_el_graph(n):
        status = status_thread.get_status()
        if status is not None:
            return generate_az_el_graph(
                status["az_limits"],
                status["el_limits"],
                status["object_locs"],
                status["motor_azel"],
                status["stow_loc"],
                status["horizon_points"],
            )

    @app.callback(
        Output("text-queue-status", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_command_display(n):
        status = status_thread.get_status()
        if status is None or (
            status["queue_size"] == 0 and status["queued_item"] == "None"
        ):
            return "SRT Inactive"
        return "SRT in Use!"

    @app.callback(
        Output("command-display", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_command_display(n):
        status = status_thread.get_status()
        if status is None:
            return ""
        current_cmd = status["queued_item"]
        queue_size = status["queue_size"]
        status_string = f"""
        ##### Command Queue Status
         - Running Command: {current_cmd}
         - {queue_size} More Commands Waiting in the Queue
        """
        return status_string

    @app.callback(
        Output("az-el-graph-modal", "is_open"),
        [
            Input("az-el-graph", "clickData"),
            Input("az-el-graph-btn-yes", "n_clicks"),
            Input("az-el-graph-btn-no", "n_clicks"),
        ],
        [State("az-el-graph-modal", "is_open"), State("point-options", "value")],
    )
    def az_el_click_func(clickData, n_clicks_yes, n_clicks_no, is_open, mode):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "az-el-graph-btn-yes":
                command_thread.add_to_queue(f"{clickData['points'][0]['text']}{mode}")
            if (
                n_clicks_yes
                or n_clicks_no
                or (
                    clickData
                    and not clickData["points"][0]["text"] == "Antenna Location"
                )
            ):
                return not is_open
            return is_open

    @app.callback(
        Output("point-modal", "is_open"),
        [
            Input("btn-point-azel", "n_clicks"),
            Input("point-btn-yes", "n_clicks"),
            Input("point-btn-no", "n_clicks"),
        ],
        [
            State("point-modal", "is_open"),
            State("azimuth", "value"),
            State("elevation", "value"),
        ],
    )
    def point_click_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, az, el):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "point-btn-yes":
                command_thread.add_to_queue(f"azel {az} {el}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @app.callback(
        Output("freq-modal", "is_open"),
        [
            Input("btn-set-freq", "n_clicks"),
            Input("freq-btn-yes", "n_clicks"),
            Input("freq-btn-no", "n_clicks"),
        ],
        [State("freq-modal", "is_open"), State("frequency", "value"),],
    )
    def freq_click_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, freq):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "freq-btn-yes":
                command_thread.add_to_queue(f"freq {freq}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @app.callback(
        Output("samp-modal", "is_open"),
        [
            Input("btn-set-samp", "n_clicks"),
            Input("samp-btn-yes", "n_clicks"),
            Input("samp-btn-no", "n_clicks"),
        ],
        [State("samp-modal", "is_open"), State("samples", "value"),],
    )
    def samp_click_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, samp):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "samp-btn-yes":
                command_thread.add_to_queue(f"samp {samp}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @app.callback(
        Output("offset-modal", "is_open"),
        [
            Input("btn-set-offset", "n_clicks"),
            Input("offset-btn-yes", "n_clicks"),
            Input("offset-btn-no", "n_clicks"),
        ],
        [
            State("offset-modal", "is_open"),
            State("offset-azimuth", "value"),
            State("offset-elevation", "value"),
        ],
    )
    def offset_click_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, az, el):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "offset-btn-yes":
                command_thread.add_to_queue(f"offset {az} {el}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @app.callback(
        Output("record-modal", "is_open"),
        [
            Input("btn-start-record", "n_clicks"),
            Input("record-btn-yes", "n_clicks"),
            Input("record-btn-no", "n_clicks"),
        ],
        [State("record-modal", "is_open"), State("record-options", "value")],
    )
    def record_click_func(
        n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, record_option
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "record-btn-yes":
                command_thread.add_to_queue(f"record {record_option}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @app.callback(
        Output("signal", "children"),
        [
            Input("btn-stow", "n_clicks"),
            Input("btn-stop-record", "n_clicks"),
            Input("btn-quit", "n_clicks"),
            Input("btn-calibrate", "n_clicks"),
        ],
    )
    def cmd_button_pressed(
        n_clicks_stow, n_clicks_stop_record, n_clicks_shutdown, n_clicks_calibrate,
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "btn-stow":
                command_thread.add_to_queue("stow")
            elif button_id == "btn-stop-record":
                command_thread.add_to_queue("roff")
            elif button_id == "btn-quit":
                command_thread.add_to_queue("quit")
            elif button_id == "btn-calibrate":
                command_thread.add_to_queue("calibrate")
