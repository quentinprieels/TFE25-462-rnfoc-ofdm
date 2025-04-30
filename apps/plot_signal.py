import numpy as np
import matplotlib.pyplot as plt

filename = "signals/rx_samples_schmidl_cox.signal.fc32.dat"
is_binary = True
format = "fc32"

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

def plot_received_signal(rx_sig: np.ndarray) -> None:
    """
    Plot the received signal.
    """    
    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    fig.suptitle('Received Signal', fontsize=14, fontweight='bold')

    axs[0].plot(np.abs(rx_sig), label='Magnitude')
    axs[0].set_ylabel('Amplitude $|rx[n]|$')
    axs[0].set_title('Magnitude')
    axs[0].grid(linestyle='--')

    axs[1].plot(np.real(rx_sig), label='Real Part')
    axs[1].set_ylabel('Amplitude $\mathcal{R}{rx[n]}$')
    axs[1].set_title('Real Part')
    axs[1].grid(linestyle='--')

    axs[2].plot(np.imag(rx_sig), label='Imaginary Part')
    axs[2].set_xlabel('Sample Index [n]')
    axs[2].set_ylabel('Amplitude $\mathcal{I}{rx[n]}$')
    axs[2].set_title('Imaginary Part')
    axs[2].grid(linestyle='--')
    plt.tight_layout()
    plt.show()


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
