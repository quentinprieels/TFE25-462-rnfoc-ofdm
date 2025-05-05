import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.metric_calculator import metric_schmidl, moving_sum
from rfnoc_ofdm.detector import find_max_idx

K = 1024
CP = 128
M = 5
N = 3
threshold = 300

def get_last_sample_as_uint32(filename: str) -> tuple:
    """
    Get the last sample of the received signal as uint32 (sc16 format => 2x uint16).
    """
    with open(filename, "rb") as file:
        data = np.fromfile(file, dtype=np.uint16)
        detected_point = data[-2] * 2**16 + data[-1]
        start_forwaring = detected_point + (K // 2) * M + (CP // 2) * M
        samples_forwarded = (len(data) / 2) - start_forwaring
    return detected_point, start_forwaring, samples_forwarded


def plot_frame_with_indexes(ofdm_frame: ofdmFrame, detected_point: int, detection_idx_schmidl: int, 
                            metric: np.ndarray = None, view_title: bool = False) -> None:
    """
    Plot the received signal with the detected point and the Schmidl index.
    """
    fig, ax1 = plt.subplots(figsize=(15, 5))
    if view_title:
        plt.title("Received Signal", fontsize=14, fontweight='bold')
    
    # Left y-axis (signal amplitude)
    line1, = ax1.plot(np.abs(ofdm_frame.tsymbols_rx), alpha=0.5, label="Received Signal")
    line2, = ax1.plot([], [], color='r', linestyle='--', label="Detected Point by FPGA")
    line3, = ax1.plot([], [], color='g', linestyle='--', label="Detected Point by simulation")
    ax1.axvline(x=detected_point, color='r', linestyle='--')
    ax1.axvline(x=detection_idx_schmidl, color='g', linestyle='--')
    ax1.set_xlabel("Sample Index")
    ax1.set_ylabel("Amplitude")
    ax1.grid(linestyle='--')
    
    # Right y-axis (metric values)
    if metric is not None:
        ax2 = ax1.twinx()
        line4, = ax2.plot(metric, color='orange', label="Schmidl N metric")
        line5, = ax2.plot([], [], color='purple', linestyle='-.', label="Threshold")
        ax2.axhline(y=threshold, color='purple', linestyle='-.')
        ax2.set_ylabel("Metric Value")
    
        # Combine legends from both axes
        lines = [line1, line2, line3, line4, line5]
        labels = [line.get_label() for line in lines]
        ax1.legend(lines, labels, loc='upper right')
    else:
        # Combine legends from both axes
        lines = [line1, line2, line3]
        labels = [line.get_label() for line in lines]
        ax1.legend(lines, labels, loc='upper right')
    plt.tight_layout()
    

# For all file in the "data" folder
detected_point_errors = []
errors = {"FPGA index error": 0, "Transmitter error": 0, "Frame too short": 0, "No error": 0}
errors_plot = {"FPGA index error": False, "Transmitter error": False, "Frame too short": False, "No error": False}

for filename in os.listdir("data"):
    ofdm_signal = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod="BPSK", payload_mod="QPSK", Nt=3, Nf=1, random_seed=42)
    ofdm_signal.load_tysmbol_bin("data/" + filename, type="sc16")
    
    # FPGA detected point
    detected_point, _, _ = get_last_sample_as_uint32("data/" + filename)
    
    # Remove measurements where detected point is not possible
    if detected_point > ofdm_signal.frame_tlen:
        errors["FPGA index error"] += 1
        if errors_plot["FPGA index error"] == False:
            errors_plot["FPGA index error"] = True
            plot_frame_with_indexes(ofdm_signal, detected_point, 0)
            plt.savefig("FPGA_index_error.pdf")
            plt.close()
        continue
    
    detected_point += (K // 2) * M # compensate the L * M delay in hardware
    
    # Simulated detected point
    if len(ofdm_signal.tsymbols_rx) < ofdm_signal.frame_tlen:
        errors["Frame too short"] += 1
        if errors_plot["Frame too short"] == False:
            errors_plot["Frame too short"] = True
            plot_frame_with_indexes(ofdm_signal, detected_point, 0)
            plt.savefig("Frame_too_short.pdf")
            plt.close()
        continue
    
    _, _, M_schmidl = metric_schmidl(ofdm_signal)
    N_schmidl = moving_sum(M_schmidl, ofdm_signal.CP * ofdm_signal.M)
    detection_idx_schmidl = find_max_idx(N_schmidl, threshold=threshold)
    
    # Remove measurements where the transmitter has failed to send a complete frame
    above_threshold = N_schmidl > 75
    crossing_points = np.where(np.diff(above_threshold.astype(int)))[0]
    if len(crossing_points) != 2:
        errors["Transmitter error"] += 1
        if errors_plot["Transmitter error"] == False:
            errors_plot["Transmitter error"] = True
            plot_frame_with_indexes(ofdm_signal, detected_point, detection_idx_schmidl, metric=N_schmidl)
            plt.savefig("Transmitter_error.pdf")
            plt.close()
        continue
    
    # Calculate the error
    detected_point_error = detection_idx_schmidl - detected_point    
    detected_point_errors.append(detected_point_error)  
    errors["No error"] += 1
    if errors_plot["No error"] == False:
        errors_plot["No error"] = True
        plot_frame_with_indexes(ofdm_signal, detected_point, detection_idx_schmidl, metric=N_schmidl)
        plt.savefig("No_error.pdf")
        plt.close()

# Print and save error statistics
errors_df = pd.DataFrame.from_dict(errors, orient='index', columns=['Count'])
errors_df['Percentage'] = (errors_df['Count'] / len(os.listdir('data'))) * 100
errors_df = errors_df.sort_values(by='Count', ascending=False)
errors_df.to_csv("errors.csv", index=True)
print(errors_df)
    
# Plot the histogram of the detected point error
plt.figure(figsize=(10, 6))
# plt.title("Histogram of Detected Point Error", fontsize=14, fontweight='bold')
plt.hist(detected_point_errors, bins=50)
plt.xlabel("Detected Point Error (samples)")
plt.ylabel("Frequency")
plt.grid(linestyle='--')
plt.tight_layout()
plt.savefig("detected_point_error_histogram.pdf")
plt.show()
