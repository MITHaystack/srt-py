"""sidebar.py

Functions to Generate Sidebar

"""

import dash_html_components as html
import dash_bootstrap_components as dbc


def generate_sidebar(title, sections):
    """Generates the Sidebar for the SRT Dashboard

    Parameters
    ----------
    title : str
        Title String for the Sidebar
    sections : dict
        Dictionary of Children to Put In Sidebar

    See Also
    --------
    <https://github.com/facultyai/dash-bootstrap-components>

    Returns
    -------
    Sidebar
    """
    # we use the Row and Col components to construct the sidebar header
    # it consists of a title, and a toggle, the latter is hidden on large screens
    sidebar_header = dbc.Row(
        [
            dbc.Col(
                html.H3(title, className="display-7"),
            ),
            dbc.Col(
                [
                    html.Button(
                        # use the Bootstrap navbar-toggler classes to style
                        html.Span(className="navbar-toggler-icon"),
                        className="navbar-toggler",
                        # the navbar-toggler classes don't set color
                        style={
                            "color": "rgba(0,0,0,.5)",
                            "border-color": "rgba(0,0,0,.1)",
                        },
                        id="navbar-toggle",
                    ),
                    html.Button(
                        # use the Bootstrap navbar-toggler classes to style
                        html.Span(className="navbar-toggler-icon"),
                        className="navbar-toggler",
                        # the navbar-toggler classes don't set color
                        style={
                            "color": "rgba(0,0,0,.5)",
                            "border-color": "rgba(0,0,0,.1)",
                        },
                        id="sidebar-toggle",
                    ),
                ],
                # the column containing the toggle will be only as wide as the
                # toggle, resulting in the toggle being right aligned
                width="auto",
                # vertically align the toggle in the center
                align="center",
            ),
        ]
    )
    contents_list = []
    for section in sections:
        contents_list.append(html.Div([html.Hr()]))
        contents_list.append(sections[section])
    # use the Collapse component to animate hiding / revealing links
    sidebar = html.Div(
        [
            sidebar_header,
            dbc.Collapse(
                contents_list,
                id="collapse",
            ),
        ],
        id="sidebar",
    )
    return sidebar
