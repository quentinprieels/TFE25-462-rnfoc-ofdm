import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .utils import symbol_mapping, inverse_mapping, InputError


class ofdmFrame:
    """
    This class represents an OFDM frame, used in the considered radar-communication system.
    
    Frame structure:
    
    An OFDM frame is composed of a preamble and a payload.
    The preamble is composed of atiming synchronization symbol used to estimate the STO.
    The payload is composed of N OFDM symbols.
    
    |<----------------------------- OFDM frame ---------------------------->|
    |<--- Preamble -->|<--------------------- Payload --------------------->|
    +-----------------+-----------------+-----------------+-------...-------+
    | Timing preamble |  OFDM symbol 0  |       ...       | OFDM symbol N-1 |
    +-----------------+-----------------+-----------------+-------...-------+
    
    Payload structure:
    
    The payload contains data and pilots symbols. Pilots symbols are used to estimate the channel
    to perform radar detection, while data symbols are used to transmit data.
    Nt and Nf parameters define the pilot spacing in time and frequency domain. 
    In the example below, Nt=1 and Nf=3. The first and the last subcarrier is always included.
    
    |<------------- Subarriers ------------>|
    +---+---+---+---+---+---+---+---+---+---+
    | P | D | D | P | D | D | P | D | D | P |  |
    +---+---+---+---+---+---+---+---+---+---+  |
    | P | D | D | P | D | D | P | D | D | P | time
    +---+---+---+---+---+---+---+---+---+---+  |
    | P | D | D | P | D | D | P | D | D | P |  |
    +---+---+---+---+---+---+---+---+---+---+  v
    """
    
    _bits_per_fsymbol = {"BPSK": 1, "QPSK": 2, "16QAM": 4, "16PSK": 4}
    
    def __init__(self, K: int = 1024, CP: int = 128, M: int = 5, N: int = 10, 
                 preamble_mod: str = "BPSK", payload_mod: str = "QPSK",
                 Nt: int = 1, Nf: int = 1,
                 random_seed: int = None, verbose: bool = False
        ) -> None:       
        """
        Initialize a SchmidlAndCoxFrame.
        
        Parameters:
        - K: Number of subcarriers                                          [# of samples] >= 1
        - CP: Cyclic prefix length                                          [# of samples] >= 0
        - M: Oversampling factor                                            [# of samples] >= 1
        - N: Number OFDM symbols in the payload                             [# of samples] >= 1
        - preamble_mod: Modulation scheme for the preamble                  [BPSK, QPSK, 16QAM, 16PSK]
        - payload_mod: Modulation scheme for the payload                    [BPSK, QPSK, 16QAM, 16PSK]
        - Nt: Pilot spacing in time domain (applies only on payload)        [# of symbols] >= 1
        - Nf: Pilot spacing in frequency domain  (applies only on payload)  [# of subcarriers] >= 1
        - random_seed: Random seed for the generator                        [int]
        - verbose: Print information                                        [bool]
        - data: Data to be used as payload                                  [str]
        """   
        # Arguments validation check
        if K < 1 or CP < 0 or M < 1 or N < 1 or Nt < 1 or Nf < 1:
            raise InputError("Invalid frame parameters")
        if preamble_mod not in self._bits_per_fsymbol or payload_mod not in self._bits_per_fsymbol:
            raise InputError("Invalid modulation scheme")
        if Nt > N or Nf > K:
            raise InputError("Invalid pilot spacing")
            
        # Randomness control
        if random_seed is None:
            random_seed = np.random.default_rng().integers(0, 2**32)
            if verbose: print(f"Frame random seed: {random_seed}")
        self.generator = np.random.default_rng(random_seed)
        
        # Parameters
        self.K = K
        self.CP = CP
        self.M = M
        self.N = N
        self.preamble_mod = preamble_mod
        self.payload_mod = payload_mod
        self.Nt = Nt
        self.Nf = Nf
        self.verbose = verbose
        
        # Derived parameters
        self.preamble_tlen = (CP + K) * M
        self.payload_tlen = N * (CP + K) * M
        self.frame_tlen = self.preamble_tlen + self.payload_tlen
        
        # Generate the preamble and payload symbols
        self.fsymbols_preamble = self.generate_preamble()
        self.fsymbols_payload, self.bits_payload = self.generate_payload()
        
        # Generate the time domain symbols
        self.tsymbols = self.modulate_frame()
        
        # Received symbols
        self.tsymbols_rx = None # Placeholder for the received symbols
        self.CP_rx = None # True if the cyclic prefix is still present in the received symbols
        self.fsymbols_payload_rx = None # Placeholder for the received frequency domain symbols
        self.H_interp = None # Placeholder for the channel estimation
    

    ############################
    # Frequency domain symbols #
    ############################
    
    def get_pilots_grid(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Get the pilot grid: a matrix to represent where pilots symbols are located.
        Note: the first and the last subcarrier is always included in the pilots, same
        for first and last OFDM symbol. This ensure that we not perform any extrapolation.
        """
        pilots_idx_f = np.concatenate((np.arange(0, self.K - 1, self.Nf), [self.K - 1]))
        pilots_idx_t = np.concatenate((np.arange(0, self.N - 1, self.Nt), [self.N - 1]))
        pilots_idx_t_mesh, pilots_idx_f_mesh = np.meshgrid(pilots_idx_t, pilots_idx_f)
        return pilots_idx_t_mesh, pilots_idx_f_mesh
    
    def get_total_possible_bits_transmitted(self) -> int:
        """
        Get the total number of bits that can be transmitted in the frame.
        """
        matrix = np.ones((self.N, self.K))
        pilots_idx_t_mesh, pilots_idx_f_mesh = self.get_pilots_grid()
        matrix[pilots_idx_t_mesh.T, pilots_idx_f_mesh.T] = 0
        return int(np.sum(matrix) * self._bits_per_fsymbol[self.payload_mod])
        
    def generate_symbol(self, mod: str, bits: np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate an OFDM symbol based on the modulation scheme.
        If bits are not provided, generate random bits.
        This function generates a column vector of the (time x subcarriers) matrix.
        
        Returns:
        - fsymbol: The generated OFDM frequency domain symbol
        - bits: The bits used to generate the symbol
        """
        if mod not in self._bits_per_fsymbol:
            raise ValueError(f"Invalid modulation scheme: {mod}")
        
        if bits is None:
            n_bits = self._bits_per_fsymbol[mod] * self.K
            bits = self.generator.integers(0, 2, n_bits)
        elif len(bits) != self._bits_per_fsymbol[mod] * self.K:
            raise ValueError(f"Invalid number of bits for {mod} modulation")
            
        fsymbol = symbol_mapping(bits, mod)
        return fsymbol, bits # Shape: (K,), (K * bits_per_fsymbol,)
    
    def generate_preamble(self) -> tuple[np.ndarray]:
        """
        Generate the preamble symbol.
        Odd subcarriers are set to 0, even contains random bits.
        
        Returns:
        - fsymbol: The generated OFDM frequency domain preamble symbol
        """
        # Timing synchronization preamble
        fsymbol_t, _ = self.generate_symbol(self.preamble_mod)
        fsymbol_t[1::2] = 0 # Set odd subcarriers to 0
        return np.array([fsymbol_t]) # Shape: (1, K)

    def generate_payload(self) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        """
        Generate the payload symbols.
        
        Returns:
        - fsymbols: Matrix (N x K) containing the generated OFDM frequency domain symbols
        - bits: Matrix (N x K * bits_per_fsymbol) containing the bits used to generate the symbols
        """
        fsymbols = np.empty((self.N, self.K), dtype=complex)
        bits = np.empty((self.N, self.K * self._bits_per_fsymbol[self.payload_mod]), dtype=int)
        for i in range(self.N):
            fsymbols[i], bits[i] = self.generate_symbol(self.payload_mod)
        return fsymbols, bits # Shape: (N, K), (N, K * bits_per_fsymbol)
    
    
    ####################################
    # Time domain symbols - modulation #
    ####################################
    
    def modulate_symbols(self, fsymbols: np.ndarray) -> np.ndarray:
        """
        Modulate the given frequency domain symbols to the time domain.
        
        Parameters:
        - fsymbols: The frequency domain symbol matrix
        
        Returns:
        - out_blk: The time domain 1D array containing the modulated symbol
        """
        assert len(fsymbols.shape) == 2, "The frequency domain symbols must be a 2D matrix"
        
        ifft_I = np.sqrt(self.K * self.M) * np.fft.ifft(fsymbols, self.K * self.M)
        if self.CP == 0:
            return np.reshape(ifft_I, (ifft_I.size,)) # Shape: N * K * M
        else:
            out_blk = np.concatenate([ifft_I[:, -self.CP * self.M:], ifft_I], axis=1)
            return np.reshape(out_blk, (out_blk.size,)) # Shape: N * ((CP + K) * M)

    def modulate_frame(self) -> np.ndarray:
        """
        Modulate the frame.
        
        Returns:
        - frame: The modulated frame (1D array preambles + payload)
        - bits: The bits used to generate the frame (2D array payload data)
        """
        tpreamble = self.modulate_symbols(self.fsymbols_preamble)
        tpayload = self.modulate_symbols(self.fsymbols_payload)
        return np.concatenate([tpreamble, tpayload]) # Shape: [(CP_preamble + K) * M] + [N * ((CP + K) * M)]
    
    
    ######################################
    # Time domain symbols - demodulation #
    ######################################
    
    def demodulate_symbols(self, remove_cp_at: str = "end") -> np.ndarray:
        """
        Demodulate the given time domain symbols to the frequency domain.
        
        Parameters:
        - remove_cp_at: Where to remove the cyclic prefix (begining or end)
        
        Returns:
        - fsymbols: The frequency domain symbol matrix
        """        
        tsymbols = self.tsymbols_rx
        
        # Remove excess samples
        if len(tsymbols) > self.payload_tlen:
            if self.verbose: print(f"CAUTION: Excess samples for {self.payload_tlen} symbols, got {len(tsymbols)}. Removing excess samples.")
            tsymbols = tsymbols[:self.payload_tlen]
        
        # Check if there are enough samples
        if len(tsymbols) < self.payload_tlen:
            if self.verbose: print(f"CAUTION: Not enough samples for {self.payload_tlen} symbols, got {len(tsymbols)}. Adding zero padding.")
            zeropad = np.zeros((self.payload_tlen - len(tsymbols),))
            tsymbols = np.concatenate([tsymbols, zeropad])
            
        # Reshape the time domain symbols to a matrix and remove the cyclic prefix
        if not self.CP_rx:
            tsymbols = np.reshape(tsymbols, (self.N, (self.K) * self.M))
        elif remove_cp_at == "end":
            tsymbols = np.reshape(tsymbols, (self.N, (self.CP + self.K) * self.M))[:, :-self.CP * self.M]
        elif remove_cp_at == "begining":
            tsymbols = np.reshape(tsymbols, (self.N, (self.CP + self.K) * self.M))[:, self.CP * self.M:]
        else:
            raise ValueError("Invalid remove_cp_at value")
        
        # Perform the FFT
        fsymbols = 1/np.sqrt(self.K * self.M) * np.fft.fft(tsymbols, axis=1)
        return fsymbols[:, :self.K] # Shape: (N, K)
    
    def demodulate_frame(self, CP_rx: bool = True, remove_cp_at: str = "end", remove_first_symbol: bool = False) -> None:
        """
        Demodulate the frame.
        
        Parameters:
        - CP_rx: True if the cyclic prefix is still present in the received symbols
        - remove_cp_at: Where to remove the cyclic prefix (begining or end)
        - remove_first_symbol: Remove the first symbol (set to true if the preamble is included in tsymbols)
        """
        # Save the received symbols
        self.CP_rx = CP_rx
        if remove_first_symbol:
            self.tsymbols_rx = self.tsymbols_rx[(self.CP + self.K) * self.M:]
        
        # Demodulate the payload symbols 
        fsymbols_payload_rx = self.demodulate_symbols(remove_cp_at)
        self.fsymbols_payload_rx = fsymbols_payload_rx
    
    def estimate_channel(self) -> None:
        """
        Estimate the channel using the pilot symbols by interpolating the channel
        estimation over the entire grid.
        """        
        # Recompute the pilot grid
        pilots_idx_f = np.concatenate((np.arange(0, self.K - 1, self.Nf), [self.K - 1]))
        pilots_idx_t = np.concatenate((np.arange(0, self.N - 1, self.Nt), [self.N - 1]))
        pilots_t_mesh, pilots_f_mesh = np.meshgrid(pilots_idx_t, pilots_idx_f)
        
        # Pilot channel estimation
        pilots_tx = self.fsymbols_payload[pilots_t_mesh.T, pilots_f_mesh.T]
        pilots_rx = self.fsymbols_payload_rx[pilots_t_mesh.T, pilots_f_mesh.T]
        H_pilots = pilots_rx / pilots_tx
    
        # Prepare for interpolation over the entire grid
        t_indices = np.arange(self.N)
        f_indices = np.arange(self.K)
        
        # Create interpolator for real anf imaginary parts
        real_interp = RegularGridInterpolator(
            (pilots_idx_t, pilots_idx_f), np.real(H_pilots), method="linear", bounds_error=False, fill_value=0
        )
        imag_interp = RegularGridInterpolator(
            (pilots_idx_t, pilots_idx_f), np.imag(H_pilots), method="linear", bounds_error=False, fill_value=0
        )
        
        # Create a grid for interpolation
        grid_t, grid_f = np.meshgrid(t_indices, f_indices, indexing="ij")
        grid_points = np.array([grid_t.flatten(), grid_f.flatten()]).T
        
        # Interpolate the channel over the entire grid
        H_interp_real = real_interp(grid_points).reshape(self.N, self.K)
        H_interp_imag = imag_interp(grid_points).reshape(self.N, self.K)
        self.H_interp = H_interp_real + 1j * H_interp_imag
            
    def equalize(self) -> None:
        """
        Equalize the received symbols.
        This function estimates the channel and equalizes the received symbols.
        """
        # Estimate the channel
        self.estimate_channel()
        
        # Equalize the received symbols
        self.fsymbols_payload_rx = self.fsymbols_payload_rx / self.H_interp
    
    def compute_ber(self) -> float:
        """
        Compute the bit error rate.
        """
        # Create a mask for data symbols (True where data is present)
        pilots_idx_t_mesh, pilots_idx_f_mesh = self.get_pilots_grid()
        data_mask = np.ones((self.N, self.K), dtype=bool)
        data_mask[pilots_idx_t_mesh.T, pilots_idx_f_mesh.T] = False

        # Extract received bits on data symbols
        rx_data_symbols = self.fsymbols_payload_rx[data_mask]
        rx_bits = inverse_mapping(rx_data_symbols, self.payload_mod)

        # Extract the transmitted bits on data symbols
        tx_data_symbols = self.fsymbols_payload[data_mask]
        tx_bits = inverse_mapping(tx_data_symbols, self.payload_mod)
        
        # Compute the bit error rate
        n_errors = np.sum(tx_bits != rx_bits)
        n_total_bits = np.sum(data_mask) * self._bits_per_fsymbol[self.payload_mod]
        ber = n_errors / n_total_bits
        return ber


    #################################
    # Save/load signal to/from file #
    #################################
    
    def save_tsymbols_txt(self, filename: str = "", auto_filename: bool = False) -> str:
        """
        Save the time domain symbols to a file.
        
        Parameters:
        - filename: The name of the file to save the symbols
        """
        assert self.tsymbols.shape[0] == self.frame_tlen, "Invalid frame length"
        if auto_filename:
            filename = f"OFDM_frame_{self.K}_{self.CP}_{self.M}_{self.N}_{self.preamble_mod}_{self.payload_mod}.txt"
        
        # Create I/Q signal
        split_signal = np.zeros((self.frame_tlen * 2))
        split_signal[0::2] = np.real(self.tsymbols)
        split_signal[1::2] = np.imag(self.tsymbols)
        
        # Normalize the signal and ensure norm < 1
        split_signal = split_signal / np.max(np.abs(split_signal)) * 0.7      
        np.savetxt(filename, split_signal)
        print(f"SIG LENGTH: {self.frame_tlen}")
        print(f"2x SIG LENGTH: {split_signal.shape[0]}")
        return filename
        
    def load_tsymbols_txt(self, filename: str, ignore_zero: bool = False) -> None:
        """
        Load the time domain symbols from a file.
        
        Parameters:
        - filename: The name of the file to load the symbols
        - ignore_zero: Ignore zero samples
        - crop: Crop the signal to the expected length
        """
        data = np.loadtxt(filename)       
        if ignore_zero:
            rx_sig = rx_sig[rx_sig != 0]
        
        rx_sig = data[0::2] + 1j * data[1::2]
        rx_sig.reshape(-1, 1)
        rx_sig = np.squeeze(rx_sig)
        
        # Check the signal length
        if len(rx_sig) != self.frame_tlen:
            print(f"CAUTION: Invalid signal length: expected {self.len}, got {len(rx_sig)}\n")
        self.tsymbols_rx = rx_sig
        
    def load_tysmbol_bin(self, filename: str, ignore_zero: bool=False, type: str="fc32") -> None:
        """
        Load a file containing a I/Q signal. The file has the same format as
        the save function.        
        """
        with open(filename, "rb") as file:
            if type == "fc32":
                data = np.fromfile(file, dtype=np.float32)
            elif type == "sc16":
                data = np.fromfile(file, dtype=np.int16)
            data = data.astype(np.complex64)
            if ignore_zero:
                data = data[data != 0]
                
            rx_sig = data[0::2] + 1j * data[1::2]
            rx_sig.reshape(-1, 1)
            rx_sig = np.squeeze(rx_sig)
        
        # Check the signal length
        if len(rx_sig) != self.frame_tlen:
            if self.frame_tlen - len(rx_sig) == self.preamble_tlen:
                print(f"CAUTION: The preamble is missing, the cyclic prefix is still present in the received symbols")
                self.CP_rx = True
            else:
                print(f"CAUTION: Invalid signal length: expected {self.frame_tlen}, got {len(rx_sig)}\n")
        self.tsymbols_rx = rx_sig


    ######################
    # Channel simulation #
    ######################
    
    def add_noise(self, SNR: float) -> None:
        """
        Add AWG noise to the given frame.
        """        
        if SNR == np.inf:
            self.tsymbols_rx = self.tsymbols
            return        
        
        # Compute the average symbol‐power over payload (no CP)
        payload_td = self.tsymbols[self.preamble_tlen:]
        payload_td = payload_td.reshape(self.N, (self.CP + self.K) * self.M)
        payload_no_cp = payload_td[:, self.CP * self.M:]
        signal_power = np.mean(np.abs(payload_no_cp) ** 2)

        # Convert Eb/N0 to Es/N0 by multiplying by bits_per_symbol
        bps = self._bits_per_fsymbol[self.payload_mod]
        ebn0_lin = 10 ** (SNR / 10)
        esn0_lin = ebn0_lin * bps

        # Now get noise‐power per sample
        noise_power = signal_power / esn0_lin
        noise_std_dev = np.sqrt(noise_power / 2)

        noise_real = self.generator.normal(0, noise_std_dev, size=len(self.tsymbols))
        noise_imag = self.generator.normal(0, noise_std_dev, size=len(self.tsymbols))
        noise_frame = noise_real + 1j * noise_imag

        self.tsymbols_rx = self.tsymbols + noise_frame
