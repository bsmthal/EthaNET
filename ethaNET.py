from utils import Packet
import random
import time
import pmt
import zmq
import logging

logging.basicConfig()
logger = logging.getLogger("ethanNet")

class EthaNET:
    def __init__(self, source_addr:int=1,grc_send_addr:str="tcp://0.0.0.0:5555",grc_recv_addr:str="tcp://127.0.0.1:5556"):
        self.source_addr = source_addr
        self.send_seq_num = 0

        self.context = None
        self.grc_send_addr = grc_send_addr
        self._open_send_socket()

        self.grc_recv_addr = grc_recv_addr
        self._open_recv_socket()

    def send(self,data,dest_addr,mcs_level):
        # generate packet
        packet = Packet(mcs_level,self.send_seq_num,dest_addr,self.source_addr)

        # add encoding to the data

        #first 6 bytes are the header and the rest is payload
        packet_bytes = packet.pack(data)

        # we need to now set up the aloha scheme
        # we will try to transmit and see if we get an ACK back
        # we try at first, if we fail we do some exponential backoff and send again until we get an ack
        num_attempts = 1
        while True:
            # send our bytes through the socket
            serialized_packet_bytes = self._serialize_packet(packet_bytes)
            logger.debug(f"Sending packet to {dest_addr} with seq {self.send_seq_num}")
            self.send_socket.send(serialized_packet_bytes)

            # logger.debug(f"Listening for response from GNURADIO at {self.grc_recv_addr}")
            ack_packet = self.receive(timeout=50)
            if ack_packet is None:
                logger.debug(f"No ACK received for seq: {self.send_seq_num}")
            elif self._ack_recv(ack_packet):
                logger.debug(f"Received ACK for seq: {self.send_seq_num}")
                # increment the sequence number
                self.send_seq_num += 1
                break

            k = min(num_attempts,10) # capped at 10
            R = random.uniform(0,2**k-1)
            backoff_time = R * self._calc_frame_time(mcs_level)
            logger.debug(f"\t\tBacking off for the {num_attempts}th time. backoff {backoff_time}")
            time.sleep(backoff_time)
            num_attempts += 1 

    def receive(self, timeout=60000):
        self.recv_socket.setsockopt(zmq.RCVTIMEO, timeout)
        
        try:
            data_in = self.recv_socket.recv()
        except zmq.Again:
            return None  # Indicate timeout occurred

        # Create packet object from deserialized bytes
        packet = self._deserialize_packet(data_in)

        # Decode the encoded payload
        header = packet[:6]
        payload = packet[6:]
        
        if not Packet.validate_checksum(payload):
            logger.debug("Invalid checksum! Discarding packet")
            return None  # Explicitly return None for invalid packets

        packet = Packet.unpack_header(header)
        packet.payload = payload

        return packet

    def _open_send_socket(self):
        if self.context is None:
            self.context = zmq.Context()
        self.send_socket = self.context.socket(zmq.PUB)
        self.send_socket.bind(self.grc_send_addr)

    def _open_recv_socket(self):
        if self.context is None:
            self.context = zmq.Context()
        self.recv_socket = self.context.socket(zmq.SUB)
        self.recv_socket.connect(self.grc_recv_addr)
        self.recv_socket.setsockopt(zmq.SUBSCRIBE, b"")

    def _serialize_packet(self,packet:bytes):
        pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(packet), list(packet)))
        # Serialize PMT to a string
        return pmt.serialize_str(pdu)
    
    def _deserialize_packet(self,pdu:bytes):
        # this may be a tuple of (metadata,payload), meta data would be created by gnuradio, this may just be payload depending on what gnuradio sends
        return pmt.to_python(pmt.deserialize_str(pdu))

    # TODO
    def _calc_frame_time(self,mcs):
        return 0.01 # TODO, actually calculate what the max frame time would be for the mcs?? or should it be max time at the lowest mcs??
    
    def _ack_recv(self,packet:Packet):
        # check if the packet is an ack packet
        if packet.sequence_number != self.send_seq_num:
            return False
        if packet.payload != b"ACK":
            return False        
        return True
