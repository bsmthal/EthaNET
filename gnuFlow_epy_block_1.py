"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""
import numpy as np
from gnuradio import gr
import pmt
import logging

class ExtractStream(gr.basic_block):
    # def __init__(self, selector_tag:str="mcs_selector", length_tag_key:str="packet_len"):
    def __init__(self):
        gr.basic_block.__init__(self,
            name="Decode from Stream",
            in_sig=[np.uint8],
            out_sig=[np.uint8])
        
        self.message_port_register_out(pmt.intern("mcs_out"))
        self.message_port_register_out(pmt.intern("header_out"))
        self.message_port_register_out(pmt.intern("length_out"))
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("ExtractStream")
        self.logger.debug("ExtractStream block initialized.")

    def work(self, input_items, output_items):
        in_data = input_items[0]
        out_data = output_items[0]

        self._bit_buffer = getattr(self, "_bit_buffer", [])
        self._sample_offset = getattr(self, "_sample_offset", self.nitems_written(0))

        # Copy input to output
        out_data[:len(in_data)] = in_data

        for i, bit in enumerate(in_data):
            self._bit_buffer.append(bit & 0x01)
            self.logger.debug("Bit buffer: %s", self._bit_buffer)

            if len(self._bit_buffer) >= 48:
                byte_list = []
                for j in range(0, 48, 8):
                    byte = sum((self._bit_buffer[j + k] << (7 - k)) for k in range(8))
                    byte_list.append(byte)

                header = bytearray(byte_list[:6])
                mcs, length = header[0], header[1]

                # Publish PMT messages
                self.message_port_pub(pmt.intern("mcs_out"), pmt.from_long(mcs))
                self.message_port_pub(pmt.intern("header_out"), pmt.init_u8vector(6, header))
                self.message_port_pub(pmt.intern("length_out"), pmt.from_long(length))

                # Tag stream
                tag_offset = self._sample_offset + i - 47  # Start of 48-bit sequence
                self.add_item_tag(0, tag_offset, pmt.intern("mcs_selector"), pmt.from_long(mcs))
                self.add_item_tag(0, tag_offset, pmt.intern("packet_len"), pmt.from_long(length))

                del self._bit_buffer[:48]

        self._sample_offset += len(in_data)
        return len(in_data)

        
        