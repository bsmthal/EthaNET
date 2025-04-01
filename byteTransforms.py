import logging
import numpy as np


#################################################################
###################  CONVERSION FUNCTIONS  ######################
#################################################################


def packetToBitList(packet: bytearray) -> np.ndarray:
    binaryList = []
    for j, n in enumerate(packet):
        for i in range(8):
            binaryList.insert(j * 8, n % 2)
            n = n >> 1

    # log_bT.debug(binaryList)
    return np.array(binaryList)


def bitListToPacket(bitList: np.ndarray) -> bytearray:
    byte = 0
    count = 0
    packet = []
    # log_bt.debug(f"\tbitlist = {bitList}")
    for row in reversed(bitList):
        for bit in reversed(row):
            byte += bit << (count)
            # log_bt.debug(f"\t{count}\t{byte:08b}")
            count += 1
            if count > 7:
                count = 0
                packet.append(byte)
                byte = 0
    if count > 0:
        packet.append(byte)
    packet = bytearray(reversed(packet))
    packet = bytes(packet)
    # log_bt.debug(f"\tpacket = {packet}\n")
    return packet


def bitListToInteger(bitList: np.ndarray) -> int:
    integer = 0
    for i in range(bitList.size):
        integer += bitList[-i - 1] * 2**i
    return integer


def integerToBitList(integer: int, numBits: int) -> np.ndarray:
    bitList = np.zeros(numBits)
    binaryStr = f"{integer:0{numBits}b}"
    for i, bit in enumerate(binaryStr):
        bitList[i] = bit

    return bitList.astype(int)


# -------------------------------------------------------------------------

#################################################################
######################  FILE FUNCTIONS  #########################
#################################################################


def readPacketFromFile(fileNum: int):
    filename = f"./packets/p{fileNum}.txt"
    file = open(filename, "r")
    data = file.read()
    data = data.encode()  # converts string to bytes

    return data


# -------------------------------------------------------------------------


#################################################################
###################  STATISTICS FUNCTIONS  ######################
#################################################################


def getBER(msg1: np.ndarray, msg2: np.ndarray) -> float:
    # First check that msgs 1 & 2 have the same length
    msg1 = np.ravel(msg1)
    msg2 = np.ravel(msg2)
    if msg1.size != msg2.size:
        # log_bt.error(
        #     f"\tThe provided bit arrays have unequal length; unable to compute BER. Returning -1..."
        # )
        # log_bt.debug(f"\tmsg1 = \n{msg1}\n\tmsg2 = \n{msg2}")
        return -1.0

    # Account for every bit error
    errCount = 0
    for bit1, bit2 in zip(msg1, msg2):
        if bit1 != bit2:
            errCount += 1
    ber = float(errCount) / float(msg1.size)
    # log_bt.debug(f"\tBER={ber}")

    return ber
