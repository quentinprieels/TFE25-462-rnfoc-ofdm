import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.plotting import colors

filename = "../tests/rx_samples_schmidl_cox.signal.fc32.dat"
is_binary = True
format = "fc32"
max_idx_in_last_symbol = False
K = 1024
CP = 128
M = 5

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
        start_forwaring = detected_point + (K // 2) * M + (CP // 2) * M
        samples_forwarded = (len(data) / 2) - start_forwaring
        
        print(f"Last sample as uint32, metric maximum: {detected_point} (composed of {hex(data[-2])} and {hex(data[-1])})")
        print(f"Start forwarding index: {start_forwaring}")
        print(f"Samples forwarded: {samples_forwarded}")
    return detected_point, start_forwaring, samples_forwarded

def plot_received_signal(rx_sig: np.ndarray) -> None:
    """
    Plot the received signal.
    """        
    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    fig.suptitle('Received Signal', fontsize=14, fontweight='bold')

    axs[0].plot(np.abs(rx_sig), color=colors["signal"])
    axs[0].set_ylabel('Amplitude $|rx[n]|$')
    axs[0].set_title('Magnitude')
    axs[0].grid(linestyle='--')
    
    if max_idx_in_last_symbol:
        detected_point, start_forwaring, _ = print_last_sample_as_uint32(signal)
        axs[0].axvline(x=detected_point, color=colors["sync"], linestyle='--', label='Detected Point')
        axs[0].axvline(x=start_forwaring, color=colors["CP"], linestyle='--', label='Start Forwarding')

    axs[1].plot(np.real(rx_sig), color=colors["signal"])
    axs[1].set_ylabel('Amplitude $\mathcal{R}{rx[n]}$')
    axs[1].set_title('Real Part')
    axs[1].grid(linestyle='--')
    if max_idx_in_last_symbol:
        axs[1].axvline(x=detected_point, color=colors["sync"], linestyle='--', label='Detected Point')
        axs[1].axvline(x=start_forwaring, color=colors["CP"], linestyle='--', label='Start Forwarding')

    axs[2].plot(np.imag(rx_sig), color=colors["signal"])
    axs[2].set_xlabel('Sample Index [n]')
    axs[2].set_ylabel('Amplitude $\mathcal{I}{rx[n]}$')
    axs[2].set_title('Imaginary Part')
    axs[2].grid(linestyle='--')
    if max_idx_in_last_symbol:
        axs[2].axvline(x=detected_point, color=colors["sync"], linestyle='--', label='Detected Point')
        axs[2].axvline(x=start_forwaring, color=colors["CP"], linestyle='--', label='Start Forwarding')
        axs[2].legend(loc='lower right')
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
plt.savefig("../tests/received_signal.pdf")
plt.show()