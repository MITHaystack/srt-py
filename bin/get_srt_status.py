import zmq
import argparse
import json


if __name__ == "__main__":
    # Create the parser
    my_parser = argparse.ArgumentParser(description="Gets the Current Status of the SRT")

    # Add the arguments
    my_parser.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Host of the SRT Status Publisher",
        default="localhost"
    )
    my_parser.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port of the SRT Status Publisher",
        default=5555
    )

    # Execute the parse_args() method
    args = my_parser.parse_args()

    # Send the Command
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{args.host}:%s" % args.port)
    socket.subscribe("")
    rec = socket.recv()
    socket.close()
    dump = json.loads(rec)
    print(json.dumps(dump, sort_keys=True, indent=4))
