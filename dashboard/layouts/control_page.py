import dash
import dash_core_components as dcc
import dash_html_components as html

from .navbar import generate_navbar


def generate_layout():
    buttons = [
        html.Button('Stow', id='btn-stow', n_clicks=0),
        html.Button('AzEl', id='btn-point-azel', n_clicks=0),
        html.Button('Set Freq', id='btn-set-freq', n_clicks=0),
        html.Button('Set Offsets', id='btn-set-offset', n_clicks=0),
        html.Button('Record', id='btn-record', n_clicks=0),
    ]
    layout = html.Div([
        generate_navbar(buttons)
    ])
    return layout


def register_callbacks(app):
    pass
