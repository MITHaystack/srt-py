"""graphs.py

Contains the Code for Generating Complicated Graphs

"""

import plotly.graph_objects as go
from datetime import datetime, timezone
import numpy as np
from math import dist
from tzlocal import get_localzone
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
import astropy.units as u
from astropy.time import Time


def generate_az_el_graph(
    az_limits,
    el_limits,
    points_dict,
    current_location,
    stow_position,
    cal_position,
    horizon_points,
    beam_width,
    rotor_loc_npoint_live,
    motor_cmd_azel,
    minimal_arrows_distance,
    npoint_arrows,
    motor_type,
    station,
    display_lim,
    draw_ecliptic,
    draw_equator,
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
    beam_width : float
        Beamwidth of the antenna

    Returns
    -------
    Plotly Figure of Azimuth and Elevation Graph
    """
    fig = go.Figure(
        layout={"uirevision": True,}
    )

    az_lower_display_lim = display_lim[0]
    az_upper_display_lim = display_lim[1]
    el_lower_display_lim = display_lim[2]
    el_upper_display_lim = display_lim[3]


    # Markers for celestial objects
    fig.add_trace(
        go.Scatter(
            x=[points_dict[name][0] for name in points_dict],
            y=[points_dict[name][1] for name in points_dict],
            text=[name for name in points_dict],
            hoverinfo = ["text", "name"],
            name="Celestial Objects",
            mode="markers+text",
            textposition="top center",
            marker_color=["rgba(152, 0, 0, .8)" for _ in points_dict],
        )
    )

    # Real size Sun
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=points_dict["Sun"][0]-0.25,
        y0=points_dict["Sun"][1]-0.25,
        x1=points_dict["Sun"][0]+0.25,
        y1=points_dict["Sun"][1]+0.25,
        fillcolor="gold",
    )

    # Real size Moon
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=points_dict["Moon"][0]-0.25,
        y0=points_dict["Moon"][1]-0.25,
        x1=points_dict["Moon"][0]+0.25,
        y1=points_dict["Moon"][1]+0.25,
        fillcolor="silver",
    )

    # N-point scan
    if rotor_loc_npoint_live:
        # Markers
        fig.add_trace(
            go.Scatter(
                x=[i[0] for i in rotor_loc_npoint_live],
                y=[i[1] for i in rotor_loc_npoint_live],
                name="N-point scan positions",
                mode="markers",
                marker_color=["greenyellow" for _ in rotor_loc_npoint_live],
            )
        )
        # Arrows showing n-point scan route
        if npoint_arrows == True:
            if len(rotor_loc_npoint_live) >1:
                azzz = [col[0] for col in rotor_loc_npoint_live]
                elll = [col[1] for col in rotor_loc_npoint_live]
                x_end   = azzz[1:]
                x_start = azzz[:-1]
                y_end   = elll[1:]
                y_start = elll[:-1]
                for x0,y0,x1,y1 in zip(x_end, y_end, x_start, y_start):
                    fig.add_annotation(
                        x=x0,
                        y=y0,
                        ax=x1,
                        ay=y1,
                        axref = 'x',
                        ayref = 'y',
                        xref = 'x',
                        yref = 'y',
                        arrowcolor='limegreen',
                        arrowwidth=2.5,
                        arrowside='end',
                        arrowsize=1,
                        arrowhead=2,
                        opacity=0.3,
                    )

    # Arrows showing telescope route
    if dist(current_location, motor_cmd_azel) > minimal_arrows_distance:
    # If the motor moves in both axis at a time
        if motor_type in ("NONE", "ALFASPID", "PUSHROD"): # IS THIS LIST OK?
            fig.add_annotation(
                ax = current_location[0],
                ay = current_location[1],
                axref = 'x',
                ayref = 'y',
                x = motor_cmd_azel[0],
                y = motor_cmd_azel[1],
                xref = 'x',
                yref = 'y',
                arrowcolor='red',
                arrowwidth=2.5,
                arrowside='end',
                arrowsize=1,
                arrowhead=4,
                opacity=0.4,
            )
        # If the motor moves in only one of the axis at a time
        if motor_type in ("CASSI", "H180MOUNT"):
            x_start = [current_location[0], motor_cmd_azel[0]  ]
            x_end   = [motor_cmd_azel[0],   motor_cmd_azel[0]  ]
            y_start = [current_location[1], current_location[1]]
            y_end   = [current_location[1], motor_cmd_azel[1]  ]

            for x0,y0,x1,y1 in zip(x_end, y_end, x_start, y_start):
                fig.add_annotation(
                    x=x0,
                    y=y0,
                    ax=x1,
                    ay=y1,
                    axref = 'x',
                    ayref = 'y',
                    xref = 'x',
                    yref = 'y',
                    arrowcolor='red',
                    arrowwidth=2.5,
                    arrowside='end',
                    arrowsize=1,
                    arrowhead = 4,
                    opacity=0.4,
                )

    # Marker for visability, basically beamwidth with azimuth stretched out for high elevation angles.
    az_l = current_location[0]
    el_l = current_location[1]
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=az_l-.5*beam_width,
        y0=el_l-.5*beam_width,
        x1=az_l+.5*beam_width,
        y1=el_l+.5*beam_width,
        fillcolor="rgba(147,112,219, .2)",
        line=dict(
            color="RoyalBlue",
            width=1,
        ),
        showlegend=True,
        name='Visability',
    )

    fig.add_trace(
        go.Scatter(
            x=[az_l],
            y=[el_l],
            text="Antenna Location",
            name="Current Location",
            mode="markers+text",
            textposition="bottom center",
            marker = dict(
                symbol="x", 
                color = ["rgba(0, 0, 152, .8)"]
            ),
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
            marker = dict(
                symbol="diamond", 
                color = ["rgba(0, 152, 0, .8)", "rgba(0, 152, 0, .8)"]
            ),
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

    # Windrose lines and letters
    x_pos = [0, 90, 180, 270, 360]
    rose_lettter = ['<b>N</b>', '<b>E</b>', '<b>S</b>', '<b>W</b>', '<b>N</b>']
    for (a, b) in zip(x_pos ,rose_lettter):
        fig.add_annotation(dict(font=dict(color="darkgray",size=14),
                                    x=a,
                                    y=1.0,
                                    showarrow=False,
                                    text=b,
                                    textangle=0,
                                    xref="x",
                                    yref="paper"
                                )
                            )

    for val in [90, 180, 270]:
        fig.add_shape(
            type="line",
            x0=val,
            y0=-90,
            x1=val,
            y1=90,
            line=dict(
                color="LightBlue",
                width=1,
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
        # ghostwhite, azure, # https://stackoverflow.com/a/72502441/6764984
        plot_bgcolor="rgb(252,252,252)",

    )
    fig.update_xaxes(range=[az_lower_display_lim, az_upper_display_lim])
    fig.update_yaxes(range=[el_lower_display_lim, el_upper_display_lim])

    # Draw ecliptic plane
    if draw_ecliptic == True:
        ecl_el, ecl_az = generate_ecliptic_plane(station)
        fig.add_trace(
            go.Scatter(
                x=[point for point in ecl_az],
                y=[point for point in ecl_el],
                name="Ecliptic",
                mode="lines",
                opacity=0.5,
                textposition="top center",
                line = dict(color = 'MediumPurple', width = 1, dash = 'dash'),
            )
        )

    # Draw equator plane
    if draw_equator == True:
        ecl_el, ecl_az = generate_equator_plane(station)
        fig.add_trace(
            go.Scatter(
                x=[point for point in ecl_az],
                y=[point for point in ecl_el],
                name="Earth's equator",
                mode="lines",
                textposition="top center",
                line = dict(color = 'LightSkyBlue', width = 1, dash = 'dot'),
            )
        )

    return fig


def generate_power_history_graph(tsys, tcal, cal_pwr, spectrum_history, gui_timezone):
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
        return emptygraph("Time", "Calibrated Power", title="Power vs Time", height=300)
    power_time, power_vals = zip(*power_history)
    if gui_timezone == 'UTC':
        xaxis_title = "Time (UTC)"
        x_labels = [datetime.fromtimestamp(t, timezone.utc) for t in power_time]
    else:
        xaxis_title = "Time (local)"
        x_labels = [datetime.fromtimestamp(t, timezone.utc).astimezone(get_localzone()) for t in power_time]

    fig = go.Figure(
        data=go.Scatter(
            x = x_labels, y=power_vals
        ),
        layout={
            "title": "Power vs Time",
            "xaxis_title": xaxis_title,
            "yaxis_title": "Calibrated Power",
            "height": 300,
            "margin": dict(
                l=20,
                r=20,
                b=20,
                t=30,
                pad=4,
            ),
            "uirevision": True,
        },
    )
    return fig

def generate_waterfall_graph(bandwidth, cf, spectrum_history, waterfall_length, gui_timezone):
    """Generates a Waterfall Graph of Spectrum Data

    Parameters
    ----------
    bandwidth : float
        Bandwidth of the Incoming Spectra
    cf : float
        Center Frequency of the Incoming Spectra
    spectrum_history : [(int, ndarary)]
        List of Spectrum Samples

    Returns
    -------
    Plotly Graph Object of Waterfall Spectrum
    """
    waterfall = []
    timestamps = []
    if len(spectrum_history) > 0:
        spectrum_history_len = len(spectrum_history)
        how_many_spectra = min(spectrum_history_len, waterfall_length)
        spectrum_history_last_n_els = spectrum_history[:how_many_spectra]

        for t, spectrum in spectrum_history_last_n_els:
            waterfall.append(list(spectrum))
            timestamps.append(t)
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
        if gui_timezone == 'UTC':
            yaxis_title = "Time (UTC)"
        else:
            yaxis_title = "Time (local)"
        fig = go.Figure(
            layout={
                "title": "Raw Spectrum History",
                "xaxis_title": xaxis,
                "yaxis_title": yaxis_title,
                "height": 300,
                "margin": dict(
                    l=20,
                    r=20,
                    b=20,
                    t=30,
                    pad=4,
                ),
                "uirevision": True,
            },
        )
        data_range = np.linspace(-bandwidth / 2, bandwidth / 2, num=len(waterfall[0])) + cf
        if gui_timezone == 'UTC':
            y_labels = [datetime.fromtimestamp(t, timezone.utc) for t in timestamps]
        else:
            y_labels = [datetime.fromtimestamp(t, timezone.utc).astimezone(get_localzone()) for t in timestamps]

        # https://plotly.com/python/builtin-colorscales/
        fig.add_trace(
            go.Heatmap(colorbar={"title": "Temp.<br>(Unitless)"}, y=y_labels, x=data_range, 
                    z=waterfall, colorscale = 'RdBu_r')
            )

        return fig
    else:
        return ""

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
            "uirevision": True,
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


def emptygraph(xlabel, ylabel, **kwargs):
    """Creates an empty figure.

    Parameters
    ----------
    xlabel : str
        String for xlabel.
    ylabel : str
        String for ylabel.
    title : str
        String for title.
    **kwargs : int
        Hieght of the figure.

    Returns
    -------
    fig : plotly.fig
        Figure object.
    """
    height = kwargs.get('height', None)
    title = kwargs.get('title', None)
    if height and title:
        layout={"title": title, "xaxis_title": xlabel, "yaxis_title": ylabel, "height": height}
    if not height:
        layout={"title": title, "xaxis_title": xlabel, "yaxis_title": ylabel}
    if (not height) and (not title):
        layout={"xaxis_title": xlabel, "yaxis_title": ylabel}
    fig = go.Figure(layout=layout)

    return fig


def generate_npoint(az_in, el_in, d_az, d_el, pow_in, cent, sides):
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
        Resolution of power measurements in elevation direction.
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
    p_in = pow_in - pmin
    x_l = np.linspace(-0.5, 0.5, sides[0])
    y_l = np.linspace(-0.5, 0.5, sides[1])
    xm, ym = np.meshgrid(x_l, y_l)
    xf = xm.flatten()
    yf = ym.flatten()
    xaout = np.linspace(-0.5, 0.5, 100)
    xo, yo = np.meshgrid(xaout, xaout)
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
    d1 = go.Contour(z=interp_data, x=xaout, y=xaout, colorscale="Viridis")
    fig = go.Figure(
        data=d1,
        layout={
            "title": "N-Point Scan",
            "xaxis_title": "Normalized x",
            "yaxis_title": "Normalized y",
            "height": 300,
            "uirevision": True,
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

def generate_bswitch_graph(power_bswitch_live, num_beamswitches):
    fig = go.Figure(
        layout={
            "title": "Beam switch",
            "xaxis_title": "Position",
            "yaxis_title": "Power",
            "height": 300,
            "uirevision": True,
            "xaxis_range": [0.75, 3.25]
        },
    )
    x_axis_points = [1, 2, 3, 2]
    x_axis_full = x_axis_points * num_beamswitches
    power_bswitch_live_len = len(power_bswitch_live)
    x_axis = x_axis_full[:power_bswitch_live_len]
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=power_bswitch_live,
            mode='markers',
            opacity=0.5,
            marker=dict(
                color='green',
                size=10,
                line=dict(
                    color='MediumPurple',
                    width=1
                )
            ),
        )
    )
    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = [1, 2, 3],
            ticktext = ['Left offset', 'Target', 'Right offset']
        )
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

def generate_ecliptic_plane(station):
    """Generates the ecliptic plane

    Parameters
    ----------
    None

    Returns
    -------
    el, az : float, float
        1-d lists
    """

    observer_lat = station["latitude"],
    observer_lon = station["longitude"],
    observer_elevation = 0
    location = EarthLocation.from_geodetic(
        lat=observer_lat * u.deg,
        lon=observer_lon * u.deg,
        height=observer_elevation * u.m,
    )

    lon_ecl = np.linspace(0, 360, 100)
    lat_ecl = np.zeros(100)

    ecliptic_plane = SkyCoord(lon_ecl, lat_ecl, unit=u.deg, frame='barycentricmeanecliptic')
    ecliptic_altaz = ecliptic_plane.transform_to(AltAz(obstime=Time.now(), location=location))
    el, az = ecliptic_altaz.alt.deg.tolist(), ecliptic_altaz.az.deg.tolist()

    return el, az

def generate_equator_plane(station):
    """Generates the equator plane

    Parameters
    ----------
    None

    Returns
    -------
    el, az : float, float
        1-d lists
    """

    observer_lat = station["latitude"],
    observer_lon = station["longitude"],
    observer_elevation = 0
    location = EarthLocation.from_geodetic(
        lat=observer_lat * u.deg,
        lon=observer_lon * u.deg,
        height=observer_elevation * u.m,
    )

    lon_eq = np.linspace(0, 360, 100)
    lat_eq = np.zeros(100)

    equator_plane = SkyCoord(lon_eq, lat_eq, unit=u.deg)
    equator_altaz = equator_plane.transform_to(AltAz(obstime=Time.now(), location=location))
    el, az = equator_altaz.alt.deg.tolist(), equator_altaz.az.deg.tolist()

    return el, az