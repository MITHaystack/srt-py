import zmq
import argparse
from time import sleep


if __name__ == "__main__":
    # Create the parser
    my_parser = argparse.ArgumentParser(description="Sends an SRT Command")

    # Add the arguments
    my_parser.add_argument(
        "command", nargs="*", metavar="command", type=str, help="The SRT Command to Execute",
    )
    my_parser.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Host of the SRT Command Queue",
        default="localhost"
    )
    my_parser.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port of the SRT Command Queue",
        default=5556
    )

    # Execute the parse_args() method
    args = my_parser.parse_args()
    command = ""
    for part in args.command:
        command += part + " "
    print(f"Sending Command '{command}'")

    # Send the Command
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f"tcp://{args.host}:%s" % args.port)
    socket.send_string(command)
    sleep(0.1)
    socket.close()
