import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go


def generate_az_el_graph(az_limits, el_limits, points_dict):
    fig = go.Figure()

    az_lower_display_lim = 0
    az_upper_display_lim = 360
    el_lower_display_lim = 0
    el_upper_display_lim = 90

    # fig.add_scatter()

    fig.add_trace(
        go.Scatter(
            x=[points_dict[name][0] for name in points_dict],
            y=[points_dict[name][1] for name in points_dict],
            name="sin",
            mode="markers",
            marker_color="rgba(152, 0, 0, .8)",
        )
    )

    for val in az_limits:
        fig.add_shape(
            type="line",
            x0=val,
            y0=el_lower_display_lim,
            x1=val,
            y1=el_upper_display_lim,
            line=dict(color="LightCoral", width=4, dash="dashdot",),
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
        title="Azimuth-Elevation Chart",
        # yaxis=dict(
        #   scaleanchor="x",
        #   scaleratio=1,
        # )
    )
    fig.update_xaxes(range=[az_lower_display_lim, az_upper_display_lim])
    fig.update_yaxes(range=[el_lower_display_lim, el_upper_display_lim])

    return fig
