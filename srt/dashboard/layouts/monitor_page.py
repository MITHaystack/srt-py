"""monitor_page.py

Function for Generating Monitor Page and Creating Callback

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
from time import time
import base64
import io
import numpy as np

from .navbar import generate_navbar
from .graphs import (
    generate_az_el_graph,
    generate_az_time_graph,
    generate_el_time_graph,
    generate_power_history_graph,
    generate_spectrum_graph,
    generate_zoom_graph,
    # generate_npoint,
    emptygraph,
)

from astropy.table import Table

root_folder = Path(__file__).parent.parent.parent.parent


def get_all_objects(config_file="config/sky_coords.csv",):
    table = Table.read(Path(root_folder, config_file), format="ascii.csv")
    all_objects = []
    for index, row in enumerate(table):
        name = row["name"]
        all_objects.append(name)
    return all_objects


def generate_first_row():
    """Generates First Row (Power and Spectrum) Display

    Returns
    -------
    Div Containing First Row Objects
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="power-graph")],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            dcc.Graph(id="cal-spectrum-histogram"),
                            dcc.Graph(id="raw-spectrum-histogram"),
                        ],
                        className="pretty_container six columns",
                    ),
                ],
                className="flex-display",
                style={
                    "justify-content": "center",
                    "margin": "5px",
                },
            ),
        ]
    )


def generate_second_row():
    """Generates Second Row (AzEl and AzEl Zoom) Display

    Returns
    -------
    Div Containing Second Row Objects
    """
    return html.Div(
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="az-el-graph")],
                    className="pretty_container six columns",
                ),

                html.Div(
                    [dcc.Graph(id="zoom-graph")],
                    className="pretty_container six columns",
                ),
            ],
            className="flex-display",
            style={"margin": dict(l=10, r=5, t=5, b=5)},
        ),
    )


def generate_popups():
    """Generates all 'Pop-up' Modal Components

    Returns
    -------
    Div Containing all Modal Components
    """
    all_objects = get_all_objects()

    return html.Div(
        [
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
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="az-el-graph-btn-no",
                                className="ml-auto",
                                # block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="az-el-graph-modal",
            ),

            dbc.Modal(
                [
                    dbc.ModalHeader("Select Object to Observe"),
                    dbc.ModalBody(
                        [
                            dcc.Dropdown(
                                all_objects, placeholder='Select an Object', id='obj-dropdown')
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="obs-obj-btn-yes",
                                className="ml-auto",
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="obs-obj-btn-no",
                                className="ml-auto",
                                # block=True,
                                color="secondary",
                            ),
                        ]

                    ),
                ],
                id="obs-obj-modal",
            ),

            dbc.Modal(
                [
                    dbc.ModalHeader("Enter Aim Coordinates"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="obj-az",
                                type="number",
                                debounce=True,
                                placeholder="Azimuth",
                            ),
                            dcc.Input(
                                id="obj-el",
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
                                id="obs-coords-btn-yes",
                                className="ml-auto",
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="obs-coords-btn-no",
                                className="ml-auto",
                                # block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="obs-coords-modal",
            ),



            dbc.Modal(
                [
                    dbc.ModalHeader("Enter Location Coordinates"),
                    dbc.ModalBody(
                        [
                            dcc.Input(
                                id="coords-lat",
                                type="number",
                                debounce=True,
                                placeholder="Latitude",
                            ),
                            dcc.Input(
                                id="coords-long",
                                type="number",
                                debounce=True,
                                placeholder="Longitude",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Yes",
                                id="coords-btn-yes",
                                className="ml-auto",
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="coords-btn-no",
                                className="ml-auto",
                                # block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="coords-modal",
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
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="point-btn-no",
                                className="ml-auto",
                                # block=True,
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
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="freq-btn-no",
                                className="ml-auto",
                                # block=True,
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
                                # block=True,
                                color="primary",
                            ),
                            dbc.Button(
                                "No",
                                id="samp-btn-no",
                                className="ml-auto",
                                # block=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="samp-modal",
            ),
            # dbc.Modal(
            #     [
            #         dbc.ModalHeader("Enter the Motor Offsets"),
            #         dbc.ModalBody(
            #             [
            #                 dcc.Input(
            #                     id="offset-azimuth",
            #                     type="number",
            #                     debounce=True,
            #                     placeholder="Azimuth Offset (deg)",
            #                 ),
            #                 dcc.Input(
            #                     id="offset-elevation",
            #                     type="number",
            #                     debounce=True,
            #                     placeholder="Elevation Offset (deg)",
            #                 ),
            #             ]
            #         ),
            #         dbc.ModalFooter(
            #             [
            #                 dbc.Button(
            #                     "Yes",
            #                     id="offset-btn-yes",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="primary",
            #                 ),
            #                 dbc.Button(
            #                     "No",
            #                     id="offset-btn-no",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="secondary",
            #                 ),
            #             ]
            #         ),
            #     ],
            #     id="offset-modal",
            # ),
            # dbc.Modal(
            #     [
            #         dbc.ModalHeader("Start Recording"),
            #         dbc.ModalBody(
            #             [
            #                 html.H5("Select a File Type"),
            #                 dcc.RadioItems(
            #                     options=[
            #                         {"label": "Digital RF (Raw Data)",
            #                          "value": ""},
            #                         {
            #                             "label": ".rad Format (Spectrum)",
            #                             "value": "*.rad",
            #                         },
            #                         {
            #                             "label": ".fits Format (Spectrum)",
            #                             "value": "*.fits",
            #                         },
            #                     ],
            #                     id="record-options",
            #                     value="",
            #                 ),
            #             ]
            #         ),
            #         dbc.ModalFooter(
            #             [
            #                 dbc.Button(
            #                     "Yes",
            #                     id="record-btn-yes",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="primary",
            #                 ),
            #                 dbc.Button(
            #                     "No",
            #                     id="record-btn-no",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="secondary",
            #                 ),
            #             ]
            #         ),
            #     ],
            #     id="record-modal",
            # ),
            # dbc.Modal(
            #     [
            #         dbc.ModalHeader("Command File"),
            #         dbc.ModalBody(
            #             [
            #                 html.H4("Upload Command File"),
            #                 dcc.Upload(
            #                     id="upload-data",
            #                     children=html.Div(
            #                         ["Drag and Drop or ",
            #                             html.A("Select Files")]
            #                     ),
            #                     style={
            #                         "width": "95%",
            #                         "hSystemeight": "60px",
            #                         "lineHeight": "60px",
            #                         "borderWidth": "1px",
            #                         "borderStyle": "dashed",
            #                         "borderRadius": "5px",
            #                         "textAlign": "center",
            #                         "margin": "10px",
            #                     },
            #                     # Allow multiple files to be uploaded
            #                     multiple=False,
            #                 ),
            #                 html.Div(
            #                     id="output-data-upload", style={"text-align": "center"}
            #                 ),
            #             ]
            #         ),
            #     ],
            #     id="cmd-file-modal",
            # ),
            # dbc.Modal(
            #     [
            #         dbc.ModalHeader("Start Daemon"),
            #         dbc.ModalBody(
            #             [
            #                 html.H6(
            #                     "Are you sure you want to try to start the background SRT Process?"
            #                 ),
            #                 html.H6(
            #                     "If the process is already running, this may fail"),
            #                 html.H5(
            #                     "Process is Already Running",
            #                     id="start-warning",
            #                     style={"text-align": "center"},
            #                 ),
            #                 dcc.Dropdown(
            #                     options=[],
            #                     placeholder="Select a Config File",
            #                     id="start-config-file",
            #                 ),
            #             ]
            #         ),
            #         dbc.ModalFooter(
            #             [
            #                 dbc.Button(
            #                     "Yes",
            #                     id="start-btn-yes",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="primary",
            #                 ),
            #                 dbc.Button(
            #                     "No",
            #                     id="start-btn-no",
            #                     className="ml-auto",
            #                     # block=True,
            #                     color="secondary",
            #                 ),
            #             ]
            #         ),
            #     ],
            #     id="start-modal",
            # ),
        ]
    )


def generate_layout():
    """Generates the Basic Layout for the Monitor Page

    Returns
    -------
    layout: html.div
        Monitor Page Layout
    """
    drop_down_buttons = {
        "Coordinates": [
            dbc.DropdownMenuItem("Set Location", id="btn-set-coords"),
        ],
        "Observe": [
            dbc.DropdownMenuItem("Select Object", id="btn-obs-obj"),
            dbc.DropdownMenuItem("Enter Coordinates", id="btn-obs-coords"),
        ],
        # "Antenna": [
        #     dbc.DropdownMenuItem("Stow", id="btn-stow"),
        #     dbc.DropdownMenuItem("Set AzEl", id="btn-point-azel"),
        #     dbc.DropdownMenuItem("Set Offsets", id="btn-set-offset"),
        # ],
        "Radio": [
            dbc.DropdownMenuItem("Set Frequency", id="btn-set-freq"),
            dbc.DropdownMenuItem("Set Bandwidth", id="btn-set-samp"),
        ],
        "Routine": [
            dbc.DropdownMenuItem("Start Recording", id="btn-start-record"),
            dbc.DropdownMenuItem("Stop Recording", id="btn-stop-record"),
            dbc.DropdownMenuItem("Calibrate", id="btn-calibrate"),
            dbc.DropdownMenuItem("Upload CMD File", id="btn-cmd-file"),
        ],
        "Power": [
            dbc.DropdownMenuItem("Start Daemon", id="btn-start"),
            dbc.DropdownMenuItem("Shutdown", id="btn-quit"),
        ],
    }
    layout = html.Div(
        [
            generate_navbar(drop_down_buttons),
            generate_first_row(),
            # html.Div(
            #     [
            #         html.Div(
            #             [dcc.Graph(id="az-el-graph")],
            #             className="pretty_container six columns",
            #         ),

            #         html.Div(
            #             [dcc.Graph(id="az-el-elevation")],
            #             className="pretty_container six columns",
            #         ),
            #     ],
            #     className="flex-display",
            #     style={"margin": dict(l=10, r=5, t=5, b=5)},
            # ),
            generate_second_row(),
            html.Div([
                html.Div(
                    [
                     html.Label("Select Time Range in Minutes", style={
                                "color": "darkgray", "margin-top": "10px", "margin-left": "20px"}),
                     dcc.Slider(5, 60, 5, id="timeinput"),
                     dbc.Button("Azimuth", id="graphaz",
                                className="ml-auto",
                                color="secondary",
                                style={"margin-top": "10px",
                                       "margin-left": "20px"}
                                ),
                     dbc.Button("Elevation", id="graphel",
                                className="ml-auto",
                                color="secondary",
                                style={"margin-top": "10px",
                                       "margin-left": "10px"}
                                ),

                     dcc.Graph(id="az-el-elevation")],
                    className="pretty_container twelve columns",
                ),
            ],
                className="flex-display",
                style={"margin": dict(l=10, r=5, t=5, b=5)},
            ),
            # generate_fig_row(),
            generate_popups(),
            html.Div(id="signal", style={"display": "none"}),
        ]
    )
    return layout


def register_callbacks(
    app, config, status_thread, command_thread, raw_spectrum_thread, cal_spectrum_thread
):
    """Registers the Callbacks for the Monitor Page

    Parameters
    ----------
    app : Dash Object
        Dash Object to Set Up Callbacks to
    config : dict
        Contains All Settings for Dashboard / Daemon
    status_thread : Thread
        Thread for Getting Status from Daemon
    command_thread : Thread
        Thread for Sending Commands to Daemon
    raw_spectrum_thread : Thread
        Thread for Getting Raw Spectrum Data from Daemon
    cal_spectrum_thread : Thread
        Thread for Getting Calibrated Spectrum Data from Daemon

    Returns
    -------
    None
    """

    @app.callback(
        Output("cal-spectrum-histogram", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_cal_spectrum_histogram(n):
        spectrum = cal_spectrum_thread.get_spectrum()
        status = status_thread.get_status()
        if status is None or spectrum is None:
            return ""
        bandwidth = float(status["bandwidth"])
        cf = float(status["center_frequency"])
        return generate_spectrum_graph(bandwidth, cf, spectrum, is_spec_cal=True)

    @app.callback(
        Output("raw-spectrum-histogram", "figure"),
        [Input("interval-component", "n_intervals")],
    )
    def update_raw_spectrum_histogram(n):

        spectrum = raw_spectrum_thread.get_spectrum()
        status = status_thread.get_status()
        if status is None or spectrum is None:
            return ""
        bandwidth = float(status["bandwidth"])
        cf = float(status["center_frequency"])
        return generate_spectrum_graph(bandwidth, cf, spectrum, is_spec_cal=False)

    @app.callback(
        Output("power-graph",
               "figure"), [Input("interval-component", "n_intervals")]
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
        return generate_power_history_graph(tsys, tcal, cal_pwr, spectrum_history)

    @app.callback(
        Output("npoint_info", "data"),
        [Input("interval-component", "n_intervals"),
         State("npoint_info", "data")],
    )
    def npointstore(n, npdata):
        """Update the npoint track info

        Parameters
        ----------
        n : int
            number of Update intervals
        npdata : dict
            will hold N- point data.

        Returns
        -------
        npdata : dict
            Updated data for the N point scan plot.
        """
        if npdata is None:
            return {"scan_center": (0, 0)}
        status = status_thread.get_status()

        if status is None:
            return {"scan_center": (0, 0)}

        data = status["n_point_data"]
        if data:
            scan_center, maxdiff, rotor_loc, pwr_list, npsides = data
            c_azn, c_eln = scan_center
            c_az, c_el = npdata["scan_center"]
            if c_azn == c_az and c_eln == c_el:
                raise PreventUpdate
            else:
                npdata["scan_center"] = scan_center
                npdata["maxdiff"] = maxdiff
                npdata["rotor_loc"] = rotor_loc
                npdata["pwr"] = pwr_list
                npdata["sides"] = npsides
                return npdata
        else:
            raise PreventUpdate

    @app.callback(
        Output("start-warning", "children"),
        [Input("interval-component", "n_intervals")],
    )
    def update_start_daemon_warning(n):
        status = status_thread.get_status()
        if status is None:
            return "SRT Daemon Not Detected"
        latest_time = status["time"]
        if time() - latest_time < 10:
            return "SRT Daemon Already On!"
        else:
            return "SRT Daemon Disconnected"

    @app.callback(
        Output("start-config-file", "options"),
        [Input("interval-component", "n_intervals")],
    )
    def update_start_daemon_options(n):
        files = [
            {"label": file.name, "value": file.name}
            for file in Path(config["CONFIG_DIR"]).glob("*")
            if file.is_file() and file.name.endswith(".yaml")
        ]
        return files

    @app.callback(
        Output("output-data-upload", "children"),
        [Input("upload-data", "contents")],
        [State("upload-data", "filename"),
         State("upload-data", "last_modified")],
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
        Output("az-el-graph",
               "figure"), [Input("interval-component", "n_intervals")]
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
                status["cal_loc"],
                status["horizon_points"],
                status["beam_width"],
            )
        return ""

    @app.callback(
        Output("zoom-graph",
               "figure"), [Input("interval-component", "n_intervals")]
    )
    def update_zoom_graph(n):
        status = status_thread.get_status()
        if status is not None:
            return generate_zoom_graph(
                status["az_limits"],
                status["el_limits"],
                status["object_locs"],
                status["motor_azel"],
                status["stow_loc"],
                status["cal_loc"],
                status["horizon_points"],
                status["beam_width"],
            )
        return ""

    @app.callback(
        Output("az-el-elevation",
               "figure"),
        [
            Input("interval-component", "n_intervals"),
            Input("graphaz", "n_clicks_timestamp"),
            Input("graphel", "n_clicks_timestamp"),
            Input("timeinput", "value")]
    )
    def update_az_el_time_graph(n, clicksaz, clicksel, range):
        status = status_thread.get_status()
        if not clicksel:
            axisstatus = 0
        elif not clicksaz:
            axisstatus = 1
        elif clicksaz > clicksel:
            axisstatus = 0
        elif clicksaz < clicksel:
            axisstatus = 1

        if status is not None:
            # if (not clicksaz and not clicksel) or clicksaz > clicksel:
            # if clicksaz > clicksel:
            if axisstatus == 0:
                return generate_az_time_graph(
                    status["az_limits"],
                    status["el_limits"],
                    status["object_locs"],
                    status["object_time_locs"],
                    status["motor_azel"],
                    status["stow_loc"],
                    status["cal_loc"],
                    status["horizon_points"],
                    status["beam_width"],
                    range
                )
            # if clicksaz < clicksel:
            if axisstatus == 1:
                return generate_el_time_graph(
                    status["az_limits"],
                    status["el_limits"],
                    status["object_locs"],
                    status["object_time_locs"],
                    status["motor_azel"],
                    status["stow_loc"],
                    status["cal_loc"],
                    status["horizon_points"],
                    status["beam_width"],
                    range
                )
        return ""

    @ app.callback(
        Output("az-el-graph-modal", "is_open"),
        [
            Input("az-el-graph", "clickData"),
            Input("az-el-graph-btn-yes", "n_clicks"),
            Input("az-el-graph-btn-no", "n_clicks"),
        ],
        [State("az-el-graph-modal", "is_open"),
         State("point-options", "value")],
    )
    def az_el_click_func(clickData, n_clicks_yes, n_clicks_no, is_open, mode):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "az-el-graph-btn-yes":
                command_thread.add_to_queue(
                    f"{clickData['points'][0]['text']}{mode}")
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

    @ app.callback(
        Output("obs-obj-modal", "is_open"),
        [
            Input("btn-obs-obj", "n_clicks"),
            Input("obs-obj-btn-yes", "n_clicks"),
            Input("obs-obj-btn-no", "n_clicks"),
        ],
        [State("obs-obj-modal", "is_open"),
         State("obj-dropdown", "value")
         ],
    )
    def set_obs_obj_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, object):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "obs-obj-btn-yes":
                command_thread.add_to_queue(f"object {object}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @ app.callback(
        Output("obs-coords-modal", "is_open"),
        [
            Input("btn-obs-coords", "n_clicks"),
            Input("obs-coords-btn-yes", "n_clicks"),
            Input("obs-coords-btn-no", "n_clicks"),
        ],
        [State("obs-coords-modal", "is_open"),
         State("obj-az", "value"),
         State("obj-el", "value")
         ],
    )
    def set_obs_coords_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, az, el):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "obs-coords-btn-yes":
                command_thread.add_to_queue(f"obj_coords {az} {el}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @ app.callback(
        Output("coords-modal", "is_open"),
        [
            Input("btn-set-coords", "n_clicks"),
            Input("coords-btn-yes", "n_clicks"),
            Input("coords-btn-no", "n_clicks"),
        ],
        [State("coords-modal", "is_open"),
         State("coords-lat", "value"),
         State("coords-long", "value")],
    )
    def coords_click_func(n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, lat, long):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "coords-btn-yes":
                command_thread.add_to_queue(f"coords {lat} {long}")
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @ app.callback(
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

    @ app.callback(
        Output("freq-modal", "is_open"),
        [
            Input("btn-set-freq", "n_clicks"),
            Input("freq-btn-yes", "n_clicks"),
            Input("freq-btn-no", "n_clicks"),
        ],
        [
            State("freq-modal", "is_open"),
            State("frequency", "value"),
        ],
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

    @ app.callback(
        Output("samp-modal", "is_open"),
        [
            Input("btn-set-samp", "n_clicks"),
            Input("samp-btn-yes", "n_clicks"),
            Input("samp-btn-no", "n_clicks"),
        ],
        [
            State("samp-modal", "is_open"),
            State("samples", "value"),
        ],
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

    @ app.callback(
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

    @ app.callback(
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

    @ app.callback(
        Output("cmd-file-modal", "is_open"),
        [
            Input("btn-cmd-file", "n_clicks"),
        ],
        [State("cmd-file-modal", "is_open")],
    )
    def cmd_file_click_func(n_clicks_btn, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            if n_clicks_btn:
                return not is_open
            return is_open

    @ app.callback(
        Output("start-modal", "is_open"),
        [
            Input("btn-start", "n_clicks"),
            Input("start-btn-yes", "n_clicks"),
            Input("start-btn-no", "n_clicks"),
        ],
        [State("start-modal", "is_open"), State("start-config-file", "value")],
    )
    def start_click_func(
        n_clicks_btn, n_clicks_yes, n_clicks_no, is_open, config_file_name
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "start-btn-yes":
                try:

                    def run_srt_daemon(configuration_dir, configuration_dict):
                        from srt.daemon import daemon as srt_d

                        daemon = srt_d.SmallRadioTelescopeDaemon(
                            configuration_dir, configuration_dict
                        )
                        daemon.srt_daemon_main()

                    from srt import config_loader
                    from multiprocessing import Process

                    config_path = Path(config["CONFIG_DIR"], config_file_name)
                    config_dict = config_loader.load_yaml(config_path)
                    daemon_process = Process(
                        target=run_srt_daemon,
                        args=(config["CONFIG_DIR"], config_dict),
                        name="SRT-Daemon",
                    )
                    daemon_process.start()
                except Exception as e:
                    print(str(e))
            if n_clicks_yes or n_clicks_no or n_clicks_btn:
                return not is_open
            return is_open

    @ app.callback(
        Output("signal", "children"),
        [
            Input("btn-stow", "n_clicks"),
            Input("btn-stop-record", "n_clicks"),
            Input("btn-quit", "n_clicks"),
            Input("btn-calibrate", "n_clicks"),
        ],
    )
    def cmd_button_pressed(
        n_clicks_stow,
        n_clicks_stop_record,
        n_clicks_shutdown,
        n_clicks_calibrate,
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""
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
