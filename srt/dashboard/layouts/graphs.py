"""graphs.py

Contains the Code for Generating Complicated Graphs

"""

import plotly.graph_objects as go
from datetime import datetime
import numpy as np


def generate_az_el_graph(
    az_limits,
    el_limits,
    points_dict,
    current_location,
    stow_position,
    cal_position,
    horizon_points,
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
    cal_position : (float, float)
        Location of the Antenna for Comparative Calibration
    horizon_points : list((float, float))
        Points to Build Outline of Horizon of Interfering Objects (i.e. Skyline in AzEl)

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
            x=[stow_position[0], cal_position[0]],
            y=[stow_position[1], cal_position[1]],
            text=["Stow", "Cal"],
            name="Other Locations",
            mode="markers+text",
            textposition="top center",
            marker_color=["rgba(0, 152, 0, .8)", "rgba(0, 152, 0, .8)"],
        )
    )

    if horizon_points is not None and len(horizon_points) > 0:
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in horizon_points],
                y=[point[1] for point in horizon_points],
                name="Horizon",
                mode="lines",
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
            fillcolor="lightgrey",
        )
        fig.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=360,
            y0=-90,
            x1=az_limits[1],
            y1=90,
            fillcolor="lightgrey",
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
            fillcolor="lightgrey",
        )

    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=-90,
        x1=360,
        y1=el_limits[0],
        fillcolor="lightgrey",
    )
    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=90,
        x1=360,
        y1=el_limits[1],
        fillcolor="lightgrey",
    )

    for val in az_limits:
        fig.add_shape(
            type="line",
            x0=val,
            y0=el_lower_display_lim,
            x1=val,
            y1=el_upper_display_lim,
            line=dict(
                color="LightBlue",
                width=4,
                dash="dashdot",
            ),
        )

    for val in el_limits:
        fig.add_shape(
            type="line",
            x0=az_lower_display_lim,
            y0=val,
            x1=az_upper_display_lim,
            y1=val,
            line=dict(
                color="LightBlue",
                width=4,
                dash="dashdot",
            ),
        )

    # Set axes ranges
    fig.update_layout(
        title={
            "text": "Click to Track an Object",
            "y": 0.97,
            "x": 0.25,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin=dict(
            l=20,
            r=20,
            b=20,
            t=30,
            pad=4,
        ),
        xaxis_title="Azimuth",
        yaxis_title="Elevation",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(range=[az_lower_display_lim, az_upper_display_lim])
    fig.update_yaxes(range=[el_lower_display_lim, el_upper_display_lim])

    return fig


def generate_power_history_graph(tsys, tcal, cal_pwr, spectrum_history):
    """Generates a Graph of the Power History

    Parameters
    ----------
    tsys : float
        System Temperature of Antenna
    tcal : float
        Temperature of the Calibration Source (i.e. Trees)
    cal_pwr : float
        Power Observed during Calibration
    spectrum_history : list
        List of Spectrum Samples and Timestamps

    Returns
    -------
    Plotly Figure of Power History Graph
    """
    power_history = []
    for t, spectrum in spectrum_history:
        p = np.sum(spectrum)
        a = len(spectrum)
        pwr = (tsys + tcal) * p / (a * cal_pwr)
        power_history.insert(0, (t, pwr))
    if power_history is None or len(power_history) == 0:
        return ""
    power_time, power_vals = zip(*power_history)
    fig = go.Figure(
        data=go.Scatter(
            x=[datetime.utcfromtimestamp(t) for t in power_time], y=power_vals
        ),
        layout={
            "title": "Power vs Time",
            "xaxis_title": "Time (UTC)",
            "yaxis_title": "Calibrated Power",
            "height": 300,
            "margin": dict(
                l=20,
                r=20,
                b=20,
                t=30,
                pad=4,
            ),
        },
    )
    return fig


def generate_spectrum_graph(bandwidth, cf, spectrum, is_spec_cal):
    """Generates a Graph of Spectrum Data

    Parameters
    ----------
    bandwidth : float
        Bandwidth of the Incoming Spectra
    cf : float
        Center Frequency of the Incoming Spectra
    spectrum : ndarry
        List of Spectrum Samples
    is_spec_cal : bool
        Whether or Not spectrum is Calibrated

    Returns
    -------
    Plotly Graph Object of Spectrum Histogram
    """
    max_histogram_size = 2048
    title = "Calibrated Spectrum" if is_spec_cal else "Raw Spectrum"
    yaxis = "Temperature (K)" if is_spec_cal else "Temp. (Unitless)"
    if cf > pow(10, 9):
        cf /= pow(10, 9)
        bandwidth /= pow(10, 9)
        xaxis = "Frequency (GHz)"
    elif cf > pow(10, 6):
        cf /= pow(10, 6)
        bandwidth /= pow(10, 6)
        xaxis = "Frequency (MHz)"
    elif cf > pow(10, 3):
        cf /= pow(10, 3)
        bandwidth /= pow(10, 3)
        xaxis = "Frequency (kHz)"
    else:
        xaxis = "Frequency (Hz)"
    fig = go.Figure(
        layout={
            "title": title,
            "xaxis_title": xaxis,
            "yaxis_title": yaxis,
            "height": 150,
            "margin": dict(
                l=20,
                r=20,
                b=20,
                t=30,
                pad=4,
            ),
        },
    )
    data_range = np.linspace(-bandwidth / 2, bandwidth / 2, num=len(spectrum)) + cf
    if len(spectrum) > max_histogram_size:
        fig.add_trace(
            go.Scatter(
                x=data_range,
                y=spectrum,
                name="Spectrum",
                mode="lines",
            )
        )
    else:
        fig.add_trace(
            go.Histogram(
                xbins={
                    "size": bandwidth / len(spectrum),
                    "start": -bandwidth / 2 + cf,
                    "end": bandwidth / 2 + cf,
                },
                autobinx=False,
                x=data_range,
                y=spectrum,
                histfunc="avg",
            )
        )
    if is_spec_cal:
        fig.update_yaxes(range=[min(spectrum), max(spectrum)])
    return fig


def emptygraph(xlabel, ylabel, title):
    """Creates an empty figure.

    Parameters
    ----------
    xlabel : str
        String for xlabel.
    ylabel : str
        String for ylabel.
    title : str
        String for title.

    Returns
    -------
    fig : plotly.fig
        Figure object.
    """

    fig = go.Figure(
        layout={"title": title, "xaxis_title": xlabel, "yaxis_title": ylabel}
    )

    return fig


def generate_npoint(az_in, el_in, d_az, d_el, pow_in, cent,sides):
    """Creates the n-point graph image.

    Parameters
    ----------
    az_in : array_like
        List of azimuth locations.
    el_in : array_like
        List of elevation locations.
    d_az : float
        Resolution of power measurements in the azimuth direction.
    d_el : float
        REsolution of power measurements in elevation direction.
    pow_in : array_like
        List of power measurements for the given locations of the antenna.
    cent : array_like
        Center point of the object being imaged.
    sides : list
        Number of pointers per side.

    Returns
    -------
    fig : plotly.fig
        Figure object.
    """

    # create the output grid
    az_in = np.array(az_in)
    el_in = np.array(el_in)
    az_a = np.linspace(az_in.min(), az_in.max(), 100)
    el_a = np.linspace(el_in.min(), el_in.max(), 100)

    azout, elout = np.meshgrid(az_a, el_a)
    pow_in = np.array(pow_in)
    pmin = pow_in.min()
    p_in = pow_in-pmin
    x_l = np.linspace(-.5,.5,sides[0])
    y_l = np.linspace(-.5,.5,sides[1])
    xm, ym = np.meshgrid(x_l,y_l)
    xf = xm.flatten()
    yf = ym.flatten()
    xaout = np.linspace(-.5,.5,100)
    xo, yo = np.meshgrid(xaout,xaout)
    # Interpolate the data
    interp_data = sinc_interp2d(xf, yf, p_in, d_az, d_el, xo, yo)
    # Determine center of the object and compare to desired center.
    pow_tot = np.sum(np.sum(interp_data))
    az_center = np.sum(np.sum(interp_data * azout)) / pow_tot
    el_center = np.sum(np.sum(interp_data * elout)) / pow_tot
    az_off = az_center - cent[0]
    el_off = el_center - cent[1]
    antext0 = "Az Center {0:.2f} deg".format(az_off)
    antext1 = "El Center {0:.2f} deg".format(el_off)
    # Make the contour plot
    d1 = go.Contour(
        z=interp_data, x=xaout, y=xaout, colorscale="Viridis"
    )
    fig = go.Figure(
        data=d1,
        layout={
            "title": "N-Point Scan",
            "xaxis_title": "Normalized x",
            "yaxis_title": "Normalized y",
        },
    )
    fig.add_annotation(
        x=xaout[10],
        y=xaout[20],
        xanchor="left",
        text=antext0,
        showarrow=False,
        font=dict(family="Courier New, monospace", size=13, color="#ffffff"),
    )

    fig.add_annotation(
        x=xaout[10],
        y=xaout[10],
        text=antext1,
        xanchor="left",
        showarrow=False,
        font=dict(family="Courier New, monospace", size=13, color="#ffffff"),
    )
    return fig


def sinc_interp2d(x, y, values, dx, dy, xout, yout):
    """Perform a sinc interpolation

    Parameters
    ----------
    x : array_like
        A 1-d array of x values.
    y : array_like
        A 1-d array of y values.
    values : array_like
        A 1-d array of values that will be interpolated.
    dx : float
        Sampling rate along the x axis.
    dy : float
        Sampling rate along the y axis.
    xout : array_like
        2-d array for x axis sampling.
    yout : array_like
        2-d array for y axis sampling.

    Returns
    -------
    val_out : array_like
        2-d array for of the values at the new sampling sampling.
    """

    val_out = np.zeros_like(xout)

    for x_c, y_c, v_c in zip(x, y, values):
        x_1 = (xout - x_c) / dx
        y_1 = (yout - y_c) / dy
        val_out += float(v_c) * np.sinc(x_1) * np.sinc(y_1)

    return val_out
