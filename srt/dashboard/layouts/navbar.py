"""navbar.py

Contains Functions for Interacting with a Navbar

"""

import dash_bootstrap_components as dbc


def generate_navbar(dropdowns, title="Commands"):
    """Generates the Navbar

    Parameters
    ----------
    dropdowns : dict
        Dictionary of Buttons for Each Dropdown Menu
    title : str
        Title of the Navbar

    Returns
    -------
    NavbarSimple
    """
    navbar = dbc.NavbarSimple(
        [
            dbc.DropdownMenu(
                children=dropdowns[drop_down],
                in_navbar=True,
                label=drop_down,
                style={"display": "flex", "flexWrap": "wrap"},
                className="m-1"
            )
            for drop_down in dropdowns
        ],
        brand=title,
        brand_style={"font-size": "large"},
        color="primary",
        dark=True,
    )
    return navbar
