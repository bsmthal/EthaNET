import argparse as ap
from header import HeaderConstructor
import zmq


MAX_PAYLOAD_SIZE = 255
# MAX_PAYLOAD_SIZE = 8192
MY_ADDRESS = b"\x01"
HOST = "127.0.0.1"
PORT = 12345


def main(**kwargs):
    file = open(kwargs["file"], "r")
    fileText = file.read()
    file.close()

    payload = fileText.encode()

    dest = convertDestToBytes(kwargs["dest"])
    payloadList = []
    packetList = []

    # Split payload into chunks that can fit within packets
    while len(payload) > MAX_PAYLOAD_SIZE:
        payloadList.append(payload[:MAX_PAYLOAD_SIZE])
        payload = payload[MAX_PAYLOAD_SIZE:]
    if len(payload) > 0:
        payloadList.append(payload)

    seqNum = 0
    for p in payloadList:
        header = HeaderConstructor(
            payload=p,
            srcAddr=MY_ADDRESS,
            destAddr=dest,
            seqNum=seqNum.to_bytes(1, byteorder="big"),
            mcsVal=b"\x00",
        )
        packetList.append(header.getPacket())
        if seqNum >= 255:
            seqNum = 0
        else:
            seqNum += 1

    # Send All Packets
    context = zmq.Context()
    with context.socket(zmq.PUSH) as client_socket:
        client_socket.connect(f"tcp://{HOST}:{PORT}")
        for packet in packetList:
            client_socket.send(packet)
            # receipt = client_socket.recv()

            # if receipt == b"Shutting Down.":
            #     break
        print("Sent all.")

    return


def convertDestToBytes(destination: int) -> bytes:
    return destination.to_bytes(1, byteorder="big")


# -----------------------------------------------------------------#

if __name__ == "__main__":
    parser = ap.ArgumentParser(prog="client.py")
    parser.add_argument(
        "-f",
        "--file",
        help="Select which file to read in as payload",
        required=True,
        metavar="FILE",
        type=str,
    )
    parser.add_argument(
        "-d",
        "--dest",
        help="Destination MAC address that transmission is intended for (input integer from 0-255)",
        default=0,
        metavar="ADDR",
        type=int,
    )

    args = parser.parse_args()
    main(**vars(args))
