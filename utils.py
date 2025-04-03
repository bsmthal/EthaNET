import struct
import crc8


# ---------------------------------------------------------------------------------------------- #
# |          |          |          |          |          |          |                          | #
# |   MCS    |   LEN    |   SEQ    |   DES    |   SRC    |   CRC    |          PAYLOAD         | #
# |  1 byte  |  1 byte  |  1 byte  |  1 byte  |  1 byte  |  1 byte  |        0-256 bytes       | #
# ---------------------------------------------------------------------------------------------- #


class Packet:
    struct_format = "!BBBBBB"
    header_size = struct.calcsize(struct_format)

    def __init__(
        self,
        mcs: int,
        sequence_number: int,
        dest_addr: int,
        source_addr: int,
        checksum: bytes = None,
        message_length: int = None,
    ):
        if not 0 <= mcs < 256:
            raise ValueError(f"MCS must be a 8-bit number ({mcs}).")

        if not 0 <= sequence_number < 256:
            raise ValueError(
                f"Sequence number must be an 8-bit number ({sequence_number})."
            )
        if not 0 <= dest_addr < 256:
            raise ValueError(
                f"Destination Address must be an 8-bit number ({sequence_number})."
            )
        if not 0 <= source_addr < 256:
            raise ValueError(
                f"Source Address must be an 8-bit number ({sequence_number})."
            )
        if message_length is not None and not 0 <= sequence_number < 256:
            raise ValueError(
                f"Mesasge length must be an 8-bit number ({sequence_number})."
            )

        self.mcs = mcs
        self.sequence_number = sequence_number
        self.dest_addr = dest_addr
        self.source_addr = source_addr
        self.checksum = checksum
        self.message_length = message_length
        self.payload = None

    def __str__(self) -> str:
        return f"mcs: {self.mcs}, seqNum: {self.sequence_number}, d_addr: {self.dest_addr}, s_addr: {self.source_addr}, len: {self.message_length}, payload: {self.payload}"

    @classmethod
    def calculate_checksum(
        cls,
        mcs: int,
        message_length: int,
        sequence_number: int,
        dest_addr: int,
        source_addr: int,
        payload: bytes,
    ) -> bytes:
        data = (
            mcs.to_bytes(1, "big")
            + message_length.to_bytes(1, "big")
            + sequence_number.to_bytes(1, "big")
            + dest_addr.to_bytes(1, "big")
            + source_addr.to_bytes(1, "big")
            + payload
        )

        return crc8.crc8().reset().update(data).digest()

    def validate_checksum(self, payload):
        """Generate checksum for payload and compare to packet checksum."""
        return self.checksum == self.calculate_checksum(
            self.mcs,
            self.message_length,
            self.sequence_number,
            self.dest_addr,
            self.source_addr,
            payload,
        )

    def pack(self, payload: bytes) -> bytes:
        """Complete header and package header and payload together."""
        self.message_length = len(payload)

        if not 0 < self.message_length < 256:
            raise ValueError(
                f"Message length must be an 8-bit number ({self.message_length})."
            )

        self.payload = payload
        self.checksum = self.calculate_checksum(
            self.mcs,
            self.message_length,
            self.sequence_number,
            self.dest_addr,
            self.source_addr,
            payload,
        )

        return self.allBytes()

    def allBytes(self):
        if self.checksum is None or self.payload is None or self.message_length is None:
            raise ValueError("Not all packet fields are populated")

        # print(f"{type(self.mcs)}, {type(self.message_length)} {type(self.sequence_number)} {type(self.dest_addr)} {type(self.source_addr)} {type(self.checksum)}")

        header = struct.pack(
            self.struct_format,
            self.mcs,
            self.message_length,
            self.sequence_number,
            self.dest_addr,
            self.source_addr,
            ord(
                self.checksum
            ),  # conflicted on this, i decided to make it a decimal to keep the struct structure flowing nicely, definitely better ways of doing this
        )
        return header + self.payload

    @classmethod
    def unpack_header(cls, header):
        """Unpack complete header into a Packet."""
        if len(header) != cls.header_size:
            raise ValueError(f"Header must be {cls.header_size} bytes")

        mcs, message_length, sequence_number, d_addr, s_addr, checksum = (
            struct.unpack_from(cls.struct_format, header)
        )

        header = cls(
            mcs=mcs,
            sequence_number=sequence_number,
            checksum=checksum,
            message_length=message_length,
            dest_addr=d_addr,
            source_addr=s_addr,
        )

        return header
    

def bytes_to_bit_list(byte_data):
    """Convert a byte string or list of bytes into a list of 1s and 0s."""
    return [int(bit) for byte in byte_data for bit in f"{byte:08b}"]

def bytes_to_grouped_bit_list(byte_data):
    """Convert a byte string or list of bytes into a list of lists of bits."""
    return [[int(bit) for bit in f"{byte:08b}"] for byte in byte_data]
