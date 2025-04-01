import numpy as np
import sys
import logging

try:
    import c_code.hamm_cffi as hamm_cffi
except:
    pass


class _hamming:

    def __init__(self, order: int = 3, CFFI: bool = None):
        self.d = 3  # True for all Hamming Codes
        self.t = int(np.floor((self.d - 1) / 2))
        self.order = int(order)
        self.n = int(2**self.order - 1)
        self.k = int(self.n - self.order)
        self.H = self._genH()
        self.G = self._genG()
        self.rate = self.k / self.n
        self.CFFI = False

        # Use CFFI performance optimization if it is available and wanted
        if CFFI != None and "hamm_cffi" in sys.modules.keys():
            self.CFFI = CFFI
        if self.CFFI:
            self.G_CFFI = self.G.flatten().astype(np.uint8)
            self.H_CFFI = self.H.flatten().astype(np.uint8)
            self.gptr_bool = hamm_cffi.ffi.cast(
                "bool*", hamm_cffi.ffi.from_buffer(self.G_CFFI)
            )

    def __repr__(self):
        return f"Hamm({self.order}) object for a ({self.n},{self.k},{self.d}) code capable of correcting {self.t} errors."

    def _genH(self) -> np.ndarray:
        """Create Systematic Hamming Parity Check Matrix

        H = [ I_n-k | P^T ]

        Returns:
            np.ndarray: (n-k x n) Parity Check Matrix
        """
        H = np.zeros((self.order, self.n), dtype=int)
        for col_idx, i in enumerate(self._sortedList(2**self.order)):
            H[:, col_idx] = np.array([int(c) for c in f"{i:0{self.order}b}"[::-1]])
        return H

    def _genG(self) -> np.ndarray:
        """Create Systematic Hamming Generator Matrix

        G = [ P | I_k ]

        Returns:
            np.ndarray: (k x n) Generator Matrix
        """
        P = self.H[:, self.order :]
        G = np.hstack([P.T, np.identity(self.k, dtype=int)])
        return G

    def _sortedList(self, end: int) -> list:
        """Create list with the tuples ordered correctly

        Args:
            end (int): 2**order

        Returns:
            list: properly sorted list
        """
        unsortedList = list(range(1, end))
        sortedList = []
        for n in unsortedList:
            if n & (n - 1) == 0:  # Check for powers of 2 i.e. identity
                sortedList.append(n)
        for n in sortedList:
            unsortedList.remove(n)
        for n in unsortedList:
            sortedList.append(n)
        return sortedList


class encoder(_hamming):
    def encode(self, message: np.ndarray, encoding: str = "bool") -> np.ndarray:
        """Encode messages into codewords

        Args:
            message (np.ndarray): (number of messages x message length) matrix containing row messages
            encoding (str): 'bytes' or 'bits' for whether the message should be interpreted and returned as bytes or single information bits.

        Returns:
            np.ndarray: (number of messages x codeword length) matrix containing row codewords
        """
        # Error Checking
        if type(message) != np.ndarray:
            message = np.asarray(message, dtype=np.uint8)
        if message.dtype is not np.uint8:
            message = message.astype(np.uint8)
        if len(message.shape) != 2:
            message = message.reshape(1, -1)
            # Zero-pad the message until it's an acceptable size
            if message.size % self.k != 0:
                # log_h.warning(
                #     f"\tMessage size doesn't fit nicely with hamming codes. Padding with '_' until it does..."
                # )
                while message.size % self.k != 0:
                    # ascii value of '_' = 0x5F
                    message = np.insert(message, 0, np.array([0, 1, 0, 1, 1, 1, 1, 1]))
            message = message.reshape(-1, self.k)

        # Encoder Tree
        if encoding == "bool" and not self.CFFI:
            return np.mod(message @ self.G, 2)
        elif encoding == "bool" and self.CFFI:
            # Massage data
            numMessages = message.shape[0]
            codeword = np.zeros(numMessages * self.n, dtype=np.uint8)
            # Create pointers to numpy arrays
            mptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(message))
            cptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(codeword))
            hamm_cffi.lib.encode_bool(
                mptr, cptr, self.gptr_bool, self.n, self.k, numMessages
            )
            return codeword
        elif encoding == "bytes" and self.CFFI:
            # massage data
            numMessages = message.shape[0]
            bytesPerCodeword = np.ceil(self.n / 8)
            codeword = np.zeros(int(numMessages * bytesPerCodeword), dtype=np.uint8)
            # Create pointers to numpy arrays
            mptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(message))
            cptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(codeword))
            gptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(self.G_CFFI))
            hamm_cffi.lib.encode_byte(mptr, cptr, gptr, self.n, self.k, numMessages)
            return codeword
        else:
            raise ValueError("Invalid Arguements Entered into encode()")


class decoder(_hamming):
    def __init__(self, order: int = 3, erasure: bool = False, CFFI: bool = None):
        _hamming.__init__(self, order, CFFI=CFFI)
        self.erasure = erasure
        if self.erasure:
            self.bipolar_erasure_val = 0
            self.M = np.zeros((2**self.k // 2, self.k), dtype=int)
            j = 0
            for i in range(2**self.k):
                cw = np.array([int(c) for c in f"{i:0{self.k}b}"])
                cwComp = (cw + 1) % 2
                cwIncluded = False
                for cwTemp in self.M[0:j]:
                    if np.all(cwComp == cwTemp):
                        cwIncluded = True
                        break
                if not cwIncluded:
                    self.M[j, :] = cw
                    j += 1
            C = (self.M @ self.G) % 2
            self.CT = self.__bipolar(C)

    def __bipolar(self, message: np.ndarray):
        R = np.zeros(message.shape, dtype=int)
        m0 = message == 0
        m1 = message == 1
        R[m0] = (-1) ** 0
        R[m1] = (-1) ** 1
        i = np.logical_and(np.logical_not(m0), np.logical_not(m1))
        R[i] = self.bipolar_erasure_val
        return R

    def _decode_erasure(self, message: np.ndarray) -> np.ndarray:
        R = self.__bipolar(message)
        T = R @ self.CT.T
        if 1:
            i = np.argmax(np.abs(T), axis=1)
            comp = (np.repeat(T[np.arange(i.size), i], (self.k)) < 0).reshape(
                (-1, self.k)
            )
            m_hat = (self.M[i, :] + comp) % 2
        return m_hat

    def _decode_nonerasure(self, codeword: np.ndarray) -> np.ndarray:
        output = np.zeros((codeword.shape[0], self.k), dtype=int)
        syndrome = (codeword @ self.H.T) % 2
        for i, s in enumerate(syndrome):
            if not np.all(s == 0):
                flipLoc = np.where((self.H == s.reshape((-1, 1))).all(axis=0))[0]
                codeword[i, flipLoc] = (codeword[i, flipLoc] + 1) % 2
            output[i, :] = codeword[i, self.order :]
        return output

    def _correct_erasure(self, message: np.ndarray) -> np.ndarray:
        # NOT IMPLEMENTED
        return

    def _correct_nonerasure(self, codeword: np.ndarray) -> np.ndarray:
        output = np.zeros((codeword.shape[0], self.k), dtype=int)
        syndrome = (codeword @ self.H.T) % 2
        for i, s in enumerate(syndrome):
            if not np.all(s == 0):
                flipLoc = np.where((self.H == s.reshape((-1, 1))).all(axis=0))[0]
                codeword[i, flipLoc] = (codeword[i, flipLoc] + 1) % 2
            output[i, :] = codeword[i, self.order :]
        # print(f"codeword = \n{codeword}\noutput = \n{output}")
        return codeword

    def decode(self, codeword: np.ndarray) -> np.ndarray:
        if type(codeword) != np.ndarray:
            codeword = np.array(codeword, dtype=np.uint8)
        if codeword.dtype is not np.uint8:
            codeword = codeword.astype(np.uint8)
        if len(codeword.shape) != 2:
            codeword = codeword.reshape(-1, self.n)

        if self.CFFI and not self.erasure:
            numMessages = codeword.shape[0]
            codeword = codeword.flatten()
            # Create pointers to numpy arrays
            cptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(codeword))
            hptr = hamm_cffi.ffi.cast("bool*", hamm_cffi.ffi.from_buffer(self.H_CFFI))
            hamm_cffi.lib.decode_no_erasures_bool(
                cptr, hptr, self.n, self.k, numMessages
            )
            codeword = codeword.reshape(-1, self.n)
            return codeword[:, self.order :]
        if self.erasure:
            return self._decode_erasure(codeword)
        else:
            return self._decode_nonerasure(codeword)

    def correct(self, codeword: np.ndarray) -> np.ndarray:
        if type(codeword) != np.ndarray:
            codeword = np.array(codeword, dtype=np.uint8)
        if codeword.dtype is not np.uint8:
            codeword = codeword.astype(np.uint8)
        if len(codeword.shape) != 2:
            codeword = codeword.reshape(-1, self.n)

        if self.erasure:
            return self._correct_erasure(codeword)
        else:
            return self._correct_nonerasure(codeword)
