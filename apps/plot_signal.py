import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.plotting import colors, use_latex, long


# filename = "../data/mean_all.all/rx_samples_schmidl_cox.signal_detected_idx.sc16.dat"
filename = "../data/long_schmidl_cox.signal_detected_idx/rx_samples_schmidl_cox_meas6.signal_detected_idx.sc16.dat"
is_binary = True
format = "sc16"
max_idx_in_last_symbol = True
K = 1024
CP = 128
M = 4

def load_tsymbols_txt(filename: str) -> np.ndarray:
    """
    Load the time domain symbols from a txt file.
    """
    data = np.loadtxt(filename)    
    rx_sig = data[0::2] + 1j * data[1::2]
    rx_sig.reshape(-1, 1)
    rx_sig = np.squeeze(rx_sig)
    return rx_sig
    
def load_tysmbol_bin(filename: str, type: str="fc32") -> np.ndarray:
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
            
        rx_sig = data[0::2] + 1j * data[1::2]
        rx_sig.reshape(-1, 1)
        rx_sig = np.squeeze(rx_sig)
    return rx_sig

def print_last_sample_as_uint32(filename: str) -> tuple:
    """
    Print the last sample of the received signal as uint32 (sc16 format => 2x uint16).
    """
    with open(filename, "rb") as file:
        data = np.fromfile(file, dtype=np.uint16)
        detected_point = data[-2] * 2**16 + data[-1]
        start_forwaring = detected_point + (K // 2) * M - (CP // 2) * M
        samples_forwarded = (len(data) / 2) - start_forwaring
        
        print(f"Last sample as uint32, metric maximum: {detected_point} (composed of {hex(data[-2])} and {hex(data[-1])})")
        print(f"Start forwarding index: {start_forwaring}")
        print(f"Samples forwarded: {samples_forwarded}")
    return detected_point, start_forwaring, samples_forwarded

def plot_received_signal(rx_sig: np.ndarray) -> None:
    """
    Plot the received signal.
    """
    plt.figure(figsize=long)
    use_latex()
    plt.plot(np.abs(rx_sig), color=colors["signal"])
    plt.ylabel('Amplitude $|y[n]|$')
    plt.xlabel('Sample Index [n]')
    plt.grid(linestyle='--')
    
    if max_idx_in_last_symbol:
        detected_point, start_forwaring, _ = print_last_sample_as_uint32(filename)
        plt.axvline(x=detected_point, color=colors["sync"], linestyle='--', label='Detected Point')
        plt.axvline(x=start_forwaring, color=colors["CP"], linestyle='--', label='Start Forwarding')
        plt.legend()
    plt.tight_layout()


signal = None
if is_binary:
    if format == "fc32":
        signal = load_tysmbol_bin(filename, type="fc32")
    elif format == "sc16":
        signal = load_tysmbol_bin(filename, type="sc16")
else:
    signal = load_tsymbols_txt(filename)

print(f"Signal shape: {signal.shape}")
plot_received_signal(signal)
# plt.savefig("../data/mean_all.all/rx_samples_schmidl_cox.signal_detected_idx.sc16.pdf")
plt.show()