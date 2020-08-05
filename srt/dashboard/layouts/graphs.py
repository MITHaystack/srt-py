"""graphs.py

Contains the Code for Generating Complicated Graph

"""

import plotly.graph_objects as go


def generate_az_el_graph(
    az_limits, el_limits, points_dict, current_location, stow_position
):
    """Generates Figure for Displaying AzEl Locations

    Parameters
    ----------
    az_limits : (float, float)
        Minimum and Maximum Azimuth Limits
    el_limits : (float, float)
        Minimum and Maximum Elevation Limits
    points_dict : dict
        Dictionary of All Points Azimuth and Elevation
    current_location : (float, float)
        Current Antenna Azimuth and Elevation
    stow_position : (float, float)
        Location of the Antenna in Stow

    Returns
    -------
    Plotly Figure of Azimuth and Elevation Graph
    """
    fig = go.Figure()

    az_lower_display_lim = 0
    az_upper_display_lim = 360
    el_lower_display_lim = 0
    el_upper_display_lim = 90

    fig.add_trace(
        go.Scatter(
            x=[points_dict[name][0] for name in points_dict],
            y=[points_dict[name][1] for name in points_dict],
            text=[name for name in points_dict],
            name="Celestial Objects",
            mode="markers+text",
            textposition="top center",
            marker_color=["rgba(152, 0, 0, .8)" for _ in points_dict],
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[current_location[0]],
            y=[current_location[1]],
            text=["Antenna Location"],
            name="Current Location",
            mode="markers+text",
            textposition="bottom center",
            marker_color=["rgba(0, 0, 152, .8)"],
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[stow_position[0]],
            y=[stow_position[1]],
            text=["Stow"],
            name="Stow Location",
            mode="markers+text",
            textposition="top center",
            marker_color=["rgba(0, 152, 0, .8)"],
        )
    )

    if az_limits[0] < az_limits[1]:
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=0,
            y0=-90,
            x1=az_limits[0],
            y1=90,
            fillcolor="lightcoral",
        )
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=360,
            y0=-90,
            x1=az_limits[1],
            y1=90,
            fillcolor="lightcoral",
        )
    else:
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=az_limits[1],
            y0=-90,
            x1=az_limits[0],
            y1=90,
            fillcolor="lightcoral",
        )

    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=-90,
        x1=360,
        y1=el_limits[0],
        fillcolor="lightcoral",
    )
    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=90,
        x1=360,
        y1=el_limits[1],
        fillcolor="lightcoral",
    )

    for val in az_limits:
        fig.add_shape(
            type="line",
            x0=val,
            y0=el_lower_display_lim,
            x1=val,
            y1=el_upper_display_lim,
            line=dict(color="LightBlue", width=4, dash="dashdot",),
        )

    for val in el_limits:
        fig.add_shape(
            type="line",
            x0=az_lower_display_lim,
            y0=val,
            x1=az_upper_display_lim,
            y1=val,
            line=dict(color="LightBlue", width=4, dash="dashdot",),
        )

    # Set axes ranges
    fig.update_layout(
        title={
            "text": "Click to Track an Object",
            "y": 1.0,
            "x": 0.1,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin=dict(l=20, r=20, b=20, t=30, pad=4,),
        xaxis_title="Azimuth",
        yaxis_title="Elevation",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(range=[az_lower_display_lim, az_upper_display_lim])
    fig.update_yaxes(range=[el_lower_display_lim, el_upper_display_lim])

    return fig
