import argparse
import json
import logging
import sys
from ethaNET import EthaNET

logging.basicConfig()
logger = logging.getLogger()

def send(ethan,input_file,mtu, mcs_level,destination_addr):
    try:
        while True:
            # Read data from file
            if input_file.name == "<stdin>":
                #inform the user to input something
                logger.info("Please input data into stdin followed by Ctrl-d twice on Linux or Ctrl-z followed by Enter on Windows")
            data = input_file.read(mtu)

            # If it is zero that means we have read to EOF so we are done
            if len(data) == 0:
                break

            logger.info(f"Sending data: {data}")
            ethan.send(data,destination_addr, mcs_level)

    except KeyboardInterrupt:
        logger.info("\nExiting...")
        return
    logger.info(f"Done sending from {input_file.name}")

#TODO
def receive(ethan,num_bytes, output_file):
    pass

def main(verbose, address,grc_transmit_addr,grc_receive_addr, func, **kwargs):
    logger.setLevel(verbose)
    logger.debug(f"Creating EthaNet object with {address} addr, {grc_transmit_addr} grc_trans_addr, and {grc_receive_addr} grc_receive_addr")
    ethan = EthaNET(source_addr=address,grc_send_addr=grc_transmit_addr,grc_recv_addr=grc_receive_addr)
    func(ethan, **kwargs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("-c", "--config", required=True, type=argparse.FileType("r"))
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=1,
        help="Sets verbosity level. The more added the higher the verbosity. -vv is the highest and will print debug statements",
    )
    parser.add_argument(
        '--address',
        '-a',
        type=int,
        default=0,
        help="What is this nodes address (0) [0-255]"
    )
    parser.add_argument(
        "--grc_transmit_addr",
        type=str,
        default="tcp://*:5555",
        help="Address of ZMQ socket of gnuradio transmitter flow"
    )
    parser.add_argument(
        "--grc_receive_addr",
        type=str,
        default="tcp://voltron.byu.edu:5556",
        help="Address of ZMQ socket of gnuradio receive flow"
    )
    subparsers = parser.add_subparsers(title="mode", required=True)

    sender_parser = subparsers.add_parser("send", aliases=["s"])
    sender_parser.set_defaults(func=send)
    sender_parser.add_argument(
        "-i",
        "--input_file",
        type=argparse.FileType("rb"),
        default=sys.stdin.buffer,
        help="Input data location (stdin)"
    )
    sender_parser.add_argument(
        "--mtu",
        type=int,
        default=32,
        help="Message size length if input data needs to be chunked (32) [0-255]"
    )
    sender_parser.add_argument(
        "-m",
        "--mcs_level",
        type=int,
        default=1,
        help="Rate at which to send the message (0) [0-255]",
    )
    sender_parser.add_argument(
        "--destination_addr",
        "-d",
        type=int,
        default=0,
        help="address of node this node is attempting to send info to"
    )

    receiver_parser = subparsers.add_parser("receive", aliases=["r"])
    receiver_parser.set_defaults(func=receive)
    receiver_parser.add_argument(
        "-n",
        "--num_bytes",
        type=int,
    )
    receiver_parser.add_argument(
        "-o",
        "--output_file",
        type=argparse.FileType("wb"),
        default=sys.stdout.buffer,
    )

    args = parser.parse_args()
    args.verbose = 40 - (10 * args.verbose) if args.verbose > 0 else 0
    main(**vars(args))