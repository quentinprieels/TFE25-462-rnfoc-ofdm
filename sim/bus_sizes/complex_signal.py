import numpy as np

class complexSignal:
    """
    Class to handle complex signals.
    """    
    def _load(self, signal: np.ndarray):
        self.csignal = signal.astype(np.complex128)
        self.real_part = np.real(self.csignal).astype(np.int64)
        self.imag_part = np.imag(self.csignal).astype(np.int64)
        
    def _load_binary(self, real_part: np.ndarray, imag_part: np.ndarray, bus_size: int):
        """
        Load a binary signal represented as '0b0_0000_0000_0000' + '0b0_0000_0000_0000 * 1j'
        into the complex signal. Here, the signal has a 13 bit bus size.
        It is represented in two's complement format.
        """        
        # Extract the bit sign (1 if negative, 0 if positive)
        real_sign = (real_part >> (bus_size - 1)) & 1
        imag_sign = (imag_part >> (bus_size - 1)) & 1
        
        # Get the data part
        real_part = real_part & ((1 << (bus_size - 1)) - 1)
        imag_part = imag_part & ((1 << (bus_size - 1)) - 1)
        
        # Convert to signed integers
        real_part = np.where(real_sign, real_part - (1 << (bus_size - 1)), real_part)
        imag_part = np.where(imag_sign, imag_part - (1 << (bus_size - 1)), imag_part)
        
        # Convert to complex signal
        csignal = real_part + 1j * imag_part
        self._load(csignal)
        
    def truncate_to_16_bits(self, bus_size: int) -> None:
        """
        Truncate the complex signal to 16 bits by removing the LSB.
        """
        # Signal is already in 16 bits max
        if bus_size <= 16:
            real_part = np.real(self.csignal).astype(np.int16)
            imag_part = np.imag(self.csignal).astype(np.int16)
            csignal = real_part + 1j * imag_part
            self._load(csignal)
            return
        
        # Signal must be truncated
        real_part = np.real(self.csignal).astype(np.int64)
        imag_part = np.imag(self.csignal).astype(np.int64)
        
        # Truncate to bus size
        shift_amount = bus_size - 16
        mask = (1 << 16) - 1
        mask = mask << shift_amount

        # Apply the mask and shift to truncate
        real_part = ((real_part & mask) >> shift_amount).astype(np.int16)
        imag_part = ((imag_part & mask) >> shift_amount).astype(np.int16)

        # Convert back to complex
        csignal = real_part + 1j * imag_part
        self._load(csignal)
        
    def clip_to_16_bits(self) -> None:
        """
        Clip the complex signal to 16 bits.
        """
        real_part = np.clip(np.real(self.csignal), -32768, 32767).astype(np.int16)
        imag_part = np.clip(np.imag(self.csignal), -32768, 32767).astype(np.int16)
        csignal = real_part + 1j * imag_part
        self._load(csignal)


def read_sc16_file(filename: str) -> np.ndarray:
    """
    Load a file containing sc16 format complex samples.
    """
    with open(filename, 'rb') as file:
        data = np.fromfile(file, dtype=np.int16)
    data = data.astype(np.complex64)
    signal = data[0::2] + 1j * data[1::2]
    signal.reshape(-1, 1)
    signal = np.squeeze(signal)
    return signal


def moving_sum(signal: np.ndarray, window_size: int) -> np.ndarray:
    """
    Calculate the moving sum of a signal.
    """
    out = np.zeros(signal.shape, dtype=signal.dtype)
    for i in range(len(signal)):
        if i < window_size:
            out[i] = np.sum(signal[:i + 1])
        else:
            out[i] = out[i - 1] + signal[i] - signal[i - window_size]
    return out