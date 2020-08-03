import argparse

from srt.daemon import daemon as srt_d

if __name__ == "__main__":
    # Create the parser
    my_parser = argparse.ArgumentParser(description="Runs the SRT Daemon Application")

    # Add the arguments
    my_parser.add_argument(
        "--config_dir",
        metavar="config_dir",
        type=str,
        help="The Path to the SRT Config Directory",
        default="~/.srt-config"
    )

    # Execute the parse_args() method
    args = my_parser.parse_args()

    # Start Running Daemon
    daemon = srt_d.SmallRadioTelescopeDaemon(config_directory=args.config_dir)
    daemon.srt_daemon_main()
