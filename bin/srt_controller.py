import zmq
import argparse
import json
from pathlib import Path
from time import sleep


def status(args):
    """

    Parameters
    ----------
    args

    Returns
    -------

    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{args.host}:%s" % args.port)
    socket.subscribe("")
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    socks = dict(poller.poll(1000))
    if socket in socks and socks[socket] == zmq.POLLIN:
        rec = socket.recv()
        dump = json.loads(rec)
        print(json.dumps(dump, sort_keys=True, indent=4))
    else:
        print("SRT Daemon Not Online")
    socket.close()


def command(args):
    """

    Parameters
    ----------
    args

    Returns
    -------

    """
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f"tcp://{args.host}:%s" % args.port)
    srt_command = ""
    for part in args.command:
        srt_command += part + " "
    print(f"Sending Command '{srt_command}'")
    socket.send_string(srt_command)
    sleep(0.1)
    socket.close()


def command_file(args):
    """
    
    Parameters
    ----------
    args

    Returns
    -------

    """
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f"tcp://{args.host}:%s" % args.port)
    with open(Path(args.command_file).expanduser(), "r") as cmd_file:
        for cmd_line in cmd_file:
            cmd_line = cmd_line.strip()
            socket.send_string(cmd_line)
    sleep(0.1)
    socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="SRT Control Utility")
    sp = parser.add_subparsers()

    # Add the Status Parser
    sp_status = sp.add_parser("status", help="Gets the Current Status of the SRT")
    sp_status.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Host of the SRT Status Publisher",
        default="localhost",
    )
    sp_status.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port of the SRT Status Publisher",
        default=5555,
    )
    sp_status.set_defaults(func=status,)

    sp_command = sp.add_parser("command", help="Sends a SRT Command")
    sp_command.add_argument(
        "command",
        nargs="*",
        metavar="command",
        type=str,
        help="The SRT Command to Execute",
    )
    sp_command.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Host of the SRT Command Queue",
        default="localhost",
    )
    sp_command.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port of the SRT Command Queue",
        default=5556,
    )
    sp_command.set_defaults(func=command)

    sp_command_file = sp.add_parser(
        "command_file", help="Sends a Command File to the SRT"
    )
    sp_command_file.add_argument(
        "command_file",
        metavar="command_file",
        type=str,
        help="The SRT Command File to Execute",
    )
    sp_command_file.add_argument(
        "--host",
        metavar="host",
        type=str,
        help="The Host of the SRT Command Queue",
        default="localhost",
    )
    sp_command_file.add_argument(
        "--port",
        metavar="port",
        type=int,
        help="The Port of the SRT Command Queue",
        default=5556,
    )
    sp_command_file.set_defaults(func=command_file)

    args = parser.parse_args()
    args.func(args)
