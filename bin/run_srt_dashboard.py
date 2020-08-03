import argparse
from waitress import serve

from srt.dashboard import app as srt_app

if __name__ == "__main__":
    # Create the parser
    my_parser = argparse.ArgumentParser(description="Runs the SRT Dashboard Application")

    # Add the arguments
    my_parser.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port to Host the Dashboard on",
        default=8080,
    )

    # Add the arguments
    my_parser.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Dashboard's Host IP",
        default="0.0.0.0",
    )

    # Execute the parse_args() method
    args = my_parser.parse_args()

    # Start Running Dashboard
    serve(srt_app.server, host=args.host, port=args.port)
