import argparse as ap
from header import HeaderParser
import zmq


MY_ADDRESS = b"\x03"
HOST = "*"
PORT = 12345


def main(**kwargs):
    output_file = open("out.txt", "w")
    error_file = open("errors.txt", "w")

    context = zmq.Context()
    server_socket = context.socket(zmq.PULL)
    server_socket.bind(f"tcp://{HOST}:{PORT}")

    for i in range(100):  # Serve up to 100 clients
        try:
            packet = server_socket.recv()

            # Parse the packet
            headParse = HeaderParser(packet)
            if headParse.validate_checksum():
                if headParse.check_destination(MY_ADDRESS):
                    output_file.write(f"Payload {i:03}:\t{headParse.payload}\n")
                else:
                    error_file.write(
                        f"Not Addressed to Me. Dropping packet... \n{packet}\n\n"
                    )
            else:
                error_file.write(f"Checksum Error: \n{packet}\n\n")

            # Record Packets
            output_file.close()
            error_file.close()
            output_file = open("out.txt", "a")
            error_file = open("errors.txt", "a")

        except KeyboardInterrupt:
            print("\tExiting gracefully...\n")
            # server_socket.send(b"Shutting Down.")
            break

        # Send Client an Acknowledgement
        if i < 99:
            # server_socket.send(b"Ack.")
            pass
        else:
            pass
            # server_socket.send(b"Shutting Down.")
        print(f"Client served.")
    # ---end(for)--------------------------------#

    output_file.close()
    error_file.close()
    server_socket.close()
    return


# -----------------------------------------------------------------#

if __name__ == "__main__":
    parser = ap.ArgumentParser(prog="send.py")

    args = parser.parse_args()
    main(**vars(args))
