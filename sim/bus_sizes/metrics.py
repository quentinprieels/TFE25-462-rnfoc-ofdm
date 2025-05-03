import numpy as np

def rmse(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the Root Mean Squared Error (RMSE) between two signals.
    """
    if signal1.dtype == np.complex128 or signal1.dtype == np.complex64:
        error = np.abs(signal1 - signal2)
    else:
        error = signal1 - signal2
    return np.sqrt(np.mean(error ** 2))

def rmse_normalized(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the normalized RMSE between two signals.
    """    
    if signal1.dtype == np.complex128 or signal1.dtype == np.complex64:
        error = np.abs(signal1 - signal2)
        denom = np.sqrt(np.mean(np.abs(signal1) ** 2))
    else:
        error = signal1 - signal2
        denom = np.sqrt(np.mean(signal1 ** 2))
    return np.sqrt(np.mean(error ** 2)) / denom if denom != 0 else np.inf

def percentage_idx_diff(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate the percentage of indices where the two signals differ.
    """
    if signal1.shape != signal2.shape:
        raise ValueError("Signals must have the same shape")
    
    diff = np.abs(signal1 - signal2)
    return np.sum(diff > 0) / len(signal1) * 100


def compare_signals(signal1: np.ndarray, signal2: np.ndarray) -> dict:
    """
    Compare two signals and return a dictionary with the RMSE and the maximum difference.
    """
    if signal1.shape != signal2.shape:
        raise ValueError("Signals must have the same shape")
    
    rmse_value = rmse(signal1, signal2)
    rmse_norm_value = rmse_normalized(signal1, signal2)
    max_diff = np.max(np.abs(signal1 - signal2))
    perst_idx_diff = percentage_idx_diff(signal1, signal2)
    first_idx_diff = np.argmax(np.abs(signal1 - signal2) > 0)
    last_idx_diff = len(signal1) - np.argmax(np.abs(signal1[::-1] - signal2[::-1]) > 0) - 1
    
    return {
        "rmse": rmse_value,
        "rmse_normalized": rmse_norm_value,
        "max_diff": max_diff,
        "percentage_idx_diff": perst_idx_diff,
        "first_idx_diff": first_idx_diff,
        "last_idx_diff": last_idx_diff
    }
