import numpy as np

from .ofdm_frame import ofdmFrame

"""
Note: The `<name>_metric` functions are designed to be used with the ofdmFrame class.
      They introduce a delay of 2*L*M = K*M sampkes, where K is the number of 
      subcarriers and M is the oversampling factor.

Note: The `moving_sum` function introduces a delay of `width` samples.
"""


def moving_sum(signal: np.ndarray, width: int) -> np.ndarray:
    """
    Compute the moving sum of the signal with a given width.
    """
    signal_length = len(signal)
    sum = np.zeros(signal_length, dtype=signal.dtype)
    for i in range(signal_length):
        if i < width:
            sum[i] = np.sum(signal[:i + 1])
        else:
            sum[i] = sum[i - 1] + signal[i] - signal[i - width]
    return sum
    

def metric_schmidl(ofdm_frame: ofdmFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the Schmidl&Cox metric for the given OFDM frame as described in the paper:
    'Robust frequency and timing synchronization for OFDM'.
    """
    y = ofdm_frame.tsymbols_rx
    L = ofdm_frame.K // 2 * ofdm_frame.M
    
    # Initialize the metrics
    frame_length = len(y)
    P = np.zeros(frame_length, dtype=np.complex128)
    R = np.zeros(frame_length, dtype=np.float128)
    M = np.zeros(frame_length, dtype=np.float128)
    
    # Calculate the metrics
    for i in range(frame_length - 1):
        y_d   = y[i]
        y_dL  = y[i - L]     if i - L   >= 0 else (0j)  # Ensure valid index
        y_d2L = y[i - 2*L]   if i - 2*L >= 0 else (0j)  # Ensure valid index
        
        # 2.2 Compute the values of P(d), R(d) and M(d)
        P[i + 1] = P[i] + np.conj(y_dL) * y_d - np.conj(y_d2L) * y_dL
        R[i + 1] = R[i] + np.abs(y_d) ** 2 - np.abs(y_dL) ** 2
        M[i + 1] = np.abs(P[i + 1]) ** 2 / (R[i + 1]) ** 2 if R[i + 1] != 0 else 0
    return P, R, M


def metric_minn(ofdm_frame: ofdmFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the Schmidl&Cox metric for the given OFDM frame as described in the paper:
    'On timing offset estimation for OFDM systems'.
    """
    y = ofdm_frame.tsymbols_rx
    L = ofdm_frame.K // 2 * ofdm_frame.M
    
    # Initialize the metrics
    frame_length = len(y)
    P = np.zeros(frame_length, dtype=np.complex128)
    R = np.zeros(frame_length, dtype=np.float128)
    M = np.zeros(frame_length, dtype=np.float128)
    
    # Calculate the metrics
    for i in range(frame_length - 1):
        y_d   = y[i]
        y_dL  = y[i - L]     if i - L   >= 0 else (0j)  # Ensure valid index
        y_d2L = y[i - 2*L]   if i - 2*L >= 0 else (0j)  # Ensure valid index
        
        # 2.2 Compute the values of P(d), R(d) and M(d)
        P[i + 1] = P[i] + np.conj(y_dL) * y_d - np.conj(y_d2L) * y_dL
        R[i + 1] = R[i] + np.abs(y_d) ** 2 - np.abs(y_d2L) ** 2
        M[i + 1] = np.abs(P[i + 1]) ** 2 / (1/2 * (R[i + 1])) ** 2 if R[i + 1] != 0 else 0
    return P, R, M


def metric_wilson(ofdm_frame: ofdmFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute a modified version of the Schmidl and Cox synchronization metrics as 
    described in the paper 'A Modified Schmidl-Cox OFDM Timing Detector'.
    """
    y = ofdm_frame.tsymbols_rx
    L = ofdm_frame.K // 2 * ofdm_frame.M

    # Initialize the metrics
    frame_length = len(y)
    P = np.zeros(frame_length, dtype=np.complex128)
    R = np.zeros(frame_length, dtype=np.float128)
    RL = np.zeros(frame_length, dtype=np.float128)
    M = np.zeros(frame_length, dtype=np.float128)

    # Calculate the metrics
    for i in range(frame_length - 1):
        y_d   = y[i]
        y_dL  = y[i - L]     if i - L >= 0 else (0j)    # Ensure valid index
        y_d2L = y[i - 2*L]   if i - 2*L >= 0 else (0j)  # Ensure valid index
        
        # 2.2 Compute the values of P(d), R(d), R(d-L) and M(d)
        P[i + 1] = P[i] + np.conj(y_dL) * y_d - np.conj(y_d2L) * y_dL
        R[i + 1] = R[i] + np.abs(y_d) ** 2 - np.abs(y_d2L) ** 2
        RL[i + 1] = RL[i] + np.abs(y_dL) ** 2 - np.abs(y_d2L) ** 2
        M[i + 1] = np.abs(P[i + 1]) ** 2 / (R[i + 1] * RL[i + 1]) if R[i + 1] != 0 and RL[i + 1] != 0 else 0
    return P, R, M
