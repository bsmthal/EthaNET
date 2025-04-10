# ----------------------------------------------------------------#
# The goals of this lab are to:
# (1) Take in a block of data bits and slap a header on 'em
# (2) Send the packet through a socket
# (3) Receive the packet through a socket
# (4) Parse the header to do stuff
# (5) Strip the header to recover the data
# (6) Familiarize yourself with ZMQ
# ----------------------------------------------------------------#


# =-++++++++++++++++++ Packet Layout ++++++++++++++++++-= #

# ---------------------------------------------------------------------------------------------- #
# |          |          |          |          |          |          |                          | #
# |   MCS    |   LEN    |   SEQ    |   DES    |   SRC    |   CRC    |          PAYLOAD         | #
# |  1 byte  |  1 byte  |  1 byte  |  1 byte  |  1 byte  |  1 byte  |        0-255 bytes       | #
# ---------------------------------------------------------------------------------------------- #


class HeaderConstructor:

    def __init__(
        self,
        payload: bytes = b"default",
        srcAddr: bytes = b"\x00",
        destAddr: bytes = b"\x00",
        seqNum: bytes = b"\x00",
        mcsVal: bytes = b"\x00",
    ):
        self.payload = payload
        self.payloadLength = self._compute_payloadLength(self.payload)
        self.source = srcAddr
        self.destination = destAddr
        self.sequence = seqNum
        self.mcs = mcsVal
        self.checksum = self._compute_checksum()
        return

    def _compute_payloadLength(self, payload: bytes) -> bytes:
        return len(payload).to_bytes(1, byteorder="big")

    def _compute_checksum(self) -> bytes:
        checksum = (
            sum(self.mcs)
            + sum(self.payloadLength)
            + sum(self.sequence)
            + sum(self.destination)
            + sum(self.source)
            + sum(self.payload)
        )
        return (checksum & 0xFF).to_bytes(1, byteorder="big")

    def getPacket(self) -> bytes:
        packet = (
            self.mcs
            + self.payloadLength
            + self.sequence
            + self.destination
            + self.source
            + self.checksum
            + self.payload
        )
        return packet


class HeaderParser:
    def __init__(self, packet: bytes):
        self.packet = packet
        (
            self.mcs,
            self.payloadLength,
            self.sequence,
            self.destination,
            self.source,
            self.checksum,
            self.payload,
        ) = self._parse_packet(packet)

    def _parse_packet(self, packet: bytes):
        mcs = packet[0:1]
        payloadLength = int.from_bytes(packet[1:2], byteorder="big")
        sequence = packet[2:3]
        destination = packet[3:4]
        source = packet[4:5]
        checksum = packet[5:6]
        payload = packet[6:]

        return mcs, payloadLength, sequence, destination, source, checksum, payload

    def validate_checksum(self) -> bool:
        computed_checksum = (
            sum(self.mcs)
            + sum(self.payloadLength.to_bytes(1, byteorder="big"))
            + sum(self.sequence)
            + sum(self.destination)
            + sum(self.source)
            + sum(self.payload)
        )
        computed_checksum = (computed_checksum & 0xFF).to_bytes(1, byteorder="big")
        return computed_checksum == self.checksum

    def check_destination(self, myAddr: bytes) -> bool:
        return myAddr == self.destination
