import dash_bootstrap_components as dbc


def generate_navbar(buttons):
    navbar = dbc.NavbarSimple(
        children=buttons,
        # dbc.NavItem(dbc.NavLink("Page 1", href="#")),
        # dbc.DropdownMenu(
        #     children=[
        #         dbc.DropdownMenuItem("More pages", header=True),
        #         dbc.DropdownMenuItem("Page 2", href="#"),
        #         dbc.DropdownMenuItem("Page 3", href="#"),
        #     ],
        #     nav=True,
        #     in_navbar=True,
        #     label="More",
        # ),
        brand="Commands",
        # brand_href="#",
        color="primary",
        dark=True,
    )
    return navbar
