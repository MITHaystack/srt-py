import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ClientsideFunction

import flask
import plotly.io as pio

from layouts import control_page, monitor_page
from layouts.sidebar import generate_sidebar
from messaging.status_fetcher import StatusThread
from messaging.command_dispatcher import CommandThread


server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

statusThread = StatusThread()
statusThread.start()

command_thread = CommandThread()
command_thread.start()

pages = {"Monitor Page": "monitor-page", "Control Page": "control-page"}
refresh_time = 5000  # ms

pio.templates.default = "seaborn"
sidebar = generate_sidebar(pages)
content = html.Div(id="page-content")
layout = html.Div(
    [
        dcc.Location(id="url"),
        sidebar,
        content,
        dcc.Interval(id="interval-component", interval=refresh_time, n_intervals=0),
        html.Div(id="output-clientside")
    ],
    id="mainContainer",
    style={"height": "100vh", "min_height": "100vh", "width": "100%", 'display': 'inline-block'},
)

app.layout = layout
app.validation_layout = html.Div(
    [layout, control_page.generate_layout(), monitor_page.generate_layout()]
)
# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("page-content", "children")],
)
monitor_page.register_callbacks(app, statusThread)
control_page.register_callbacks(app, statusThread, command_thread)


@app.callback(
    [Output(f"{pages[page_name]}-link", "active") for page_name in pages],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return tuple([i == 0 for i in enumerate(pages)])
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


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", f"/{pages['Monitor Page']}"]:
        return monitor_page.generate_layout()
    elif pathname == f"/{pages['Control Page']}":
        return control_page.generate_layout()
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True)
