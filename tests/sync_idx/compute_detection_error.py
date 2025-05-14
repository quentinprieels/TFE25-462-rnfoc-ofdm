import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import colors, long
from rfnoc_ofdm.metric_calculator import metric_schmidl, moving_sum
from rfnoc_ofdm.detector import find_max_idx

folder = "../../data/long_schmidl_cox.signal_detected_idx"

K = 1024
CP = 128
M = 4
N = 256
preamble_mod = "BPSK"
payload_mod = "QPSK"
Nt = 4
Nf = 1
random_seed = 42
threshold = 300

def get_last_sample_as_uint32(filename: str) -> tuple:
    """
    Get the last sample of the received signal as uint32 (sc16 format => 2x uint16).
    """
    with open(filename, "rb") as file:
        data = np.fromfile(file, dtype=np.uint16)
        detected_point = data[-2] * 2**16 + data[-1]
        start_forwaring = detected_point + (K // 2) * M - (CP // 2) * M  # Add the detector counter delay
    return detected_point, start_forwaring

errors = []
for filename in os.listdir(folder):
    if not filename.endswith(".dat"):
        continue
    
    print(f"Processing {filename}...")
    
    # Create the frame pilots and load received data
    ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
    ofdm_frame.load_tysmbol_bin(folder + "/" + filename, type="sc16")
    
    # Get the detected point from the file
    detected_point, start_forwaring = get_last_sample_as_uint32(folder + "/" + filename)
    
    # Check that we have enough samples before detected point to perform post-processing synchronization
    if start_forwaring < ofdm_frame.preamble_tlen:
        print(f"Not enough samples before detected point in {filename}.")
        continue
    
    # Synchronization
    _, _, M_schmidl = metric_schmidl(ofdm_frame)
    N_schmidl = moving_sum(M_schmidl, ofdm_frame.CP * ofdm_frame.M)
    sync_idx = find_max_idx(N_schmidl, threshold)  - (ofdm_frame.CP // 2 * ofdm_frame.M)

    # Check plot
    # plt.figure(figsize=long)
    # plt.plot(np.abs(ofdm_frame.tsymbols_rx), label="R_schmidlReceived Signal", color=colors["signal"])
    # plt.legend()
    # plt.twinx()
    # plt.axvline(x=start_forwaring, linestyle='--', color=colors["sync"], label="Detected Point by FPGA")
    # plt.axvline(x=sync_idx, linestyle='--', color=colors["CP"], label="Detected Point by simulation")
    # plt.plot(M_schmidl, color=colors['metric'], label="Schmidl M metric", linestyle='--')
    # plt.plot(N_schmidl, color=colors['metric'], label="Schmidl N metric")
    # plt.axhline(y=threshold, color=colors['threshold'], linestyle='-.', label="Threshold")
    # plt.xlabel("Sample Index [n]")
    # plt.ylabel("Amplitude |y[n]|")
    # plt.grid(linestyle='--')
    # plt.legend()
    # plt.show()
    
    # Compute the index error
    index_error = sync_idx - start_forwaring
    errors.append((filename, index_error))
    
# Save the results to a CSV file
df = pd.DataFrame(errors, columns=['Filename', 'Index Error'])
df.reset_index(inplace=True)
df.to_csv(folder + "/sync_idx_errors_results.csv", index=False)
df.to_csv("sync_idx_errors_results.csv", index=False)
