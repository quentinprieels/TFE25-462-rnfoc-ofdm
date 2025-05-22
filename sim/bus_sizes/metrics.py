import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.plotting import colors, long, use_latex

def rmse(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the Root Mean Squared Error (RMSE) between two signals.
    """
    if signal1.dtype == np.complex128 or signal1.dtype == np.complex64:
        error = np.abs(signal1 - signal2)
    else:
        error = signal1 - signal2
    return np.sqrt(np.mean(error ** 2))

def rmse_scaled(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the RMSE between two signals, scaled to the same range.
    Returns a value normalized between 0 and 1.
    """        
    # Calculate scale factor
    scale_factor = np.max(np.abs(signal1)) / np.max(np.abs(signal2))
    if abs(scale_factor - 1) < 0.0001: scale_factor = 1  # Avoid numerical issues
    
    # Scale the second signal
    signal2_scaled = signal2 * scale_factor
    
    # Calculate error based on signal type
    if signal1.dtype == np.complex128 or signal1.dtype == np.complex64:
        error = np.abs(signal1 - signal2_scaled)
    else:
        error = signal1 - signal2_scaled
    
    # Calculate RMSE and normalize to [0,1]
    rmse_value = np.sqrt(np.mean(error ** 2))    
    return rmse_value

def percentage_idx_diff(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the percentage of indices where the two signals differ.
    """
    if signal1.shape != signal2.shape:
        raise ValueError("Signals must have the same shape")
    
    diff = np.abs(signal1 - signal2)
    return np.sum(diff > 0) / len(signal1) * 100


def compare_signals(signal1: np.ndarray, signal1_name: str, signal2: np.ndarray, signal2_name: str, plot: bool = False) -> dict:
    """
    Compare two signals and return a dictionary with the RMSE and the maximum difference.
    """
    # Set signal to the same length
    min_len = min(len(signal1), len(signal2))
    signal1 = signal1[:min_len]
    signal2 = signal2[:min_len]
    
    # Plot signals if requested
    if plot:
        signal1_name_file = signal1_name.replace(" ", "_").lower()
        signal2_name_file = signal2_name.replace(" ", "_").lower()
        
        # Scale signals to a common range for better visualization
        scale_factor = np.max(np.abs(signal1)) / np.max(np.abs(signal2))
        signal2_scaled = signal2 * scale_factor
        
        plt.figure(figsize=long)
        use_latex()
        plt.plot(np.abs(signal1), label=f"{signal1_name}", color=colors["line1"])
        plt.plot(np.abs(signal2_scaled), label=f"{signal2_name} (scaled)", linestyle='--', color=colors["line2"])
        plt.xlabel("Sample Index")
        plt.ylabel("Normalized Amplitude")
        plt.legend(loc='lower right')
        plt.grid(linestyle='--')
        plt.tight_layout()
        plt.savefig(f"results/{signal1_name_file}_vs_{signal2_name_file}.pdf")
        plt.close()
    
    # Comparison metrics calculation
    rmse_value = rmse(signal1, signal2)
    rmse_scaled_value = rmse_scaled(signal1, signal2)
    percentage_idx_diff_value = percentage_idx_diff(signal1, signal2)
    diff = np.abs(signal1 - signal2) > 0
    if not np.any(diff):
        first_idx_diff = -1
        last_idx_diff = -1
    else:
        first_idx_diff = np.argmax(diff)
        last_idx_diff = len(signal1) - np.argmax(diff[::-1]) - 1
        
    print(f"{signal1_name} vs {signal2_name}: rmse_scaled = {rmse_scaled_value:.2f}, max_signal_1 = {np.sqrt(np.max(np.abs(signal1) ** 2))}")
    
    return {
        "Base signal": signal1_name,
        "Comparison signal": signal2_name,
        "RMSE": rmse_value,
        "RMSE (scaled)": rmse_scaled_value,
        "RMSE (scale & normalized)": rmse_scaled_value / np.sqrt(np.max(np.abs(signal1) ** 2)),
        "Amount array difference [%]": percentage_idx_diff_value,
        "First index difference": first_idx_diff,
        "Last index difference": last_idx_diff
    }
