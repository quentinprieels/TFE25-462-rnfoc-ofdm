import os
from timeit import default_timer as timer
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

file_folder = "data_classical"
results = []
nb_experiments = 15


# Timing measure helper functions
def timer_func(func):
    def wrapper(*args, **kwargs):
        start = timer()
        result = func(*args, **kwargs)
        end = timer()
        results.append((func.__name__, (end - start) * 1000))  # ms
        return result
    return wrapper


# Modulation steps
@timer_func
def synchronization(ofdm_signal: ofdmFrame):
    frame_start_idx = ofdm_signal.get_frame_synchronization_idx()
    payload_start_idx = frame_start_idx + ofdm_signal.preamble_tlen
    ofdm_signal.tsymbols_rx = ofdm_signal.tsymbols_rx[payload_start_idx:]

@timer_func
def demodulation(ofdm_signal: ofdmFrame):
    ofdm_signal.demodulate_frame()

@timer_func  
def channel_estimation(ofdm_signal: ofdmFrame):
    ofdm_signal.estimate_channel()

@timer_func
def equalization(ofdm_signal: ofdmFrame):
    ofdm_signal.equalize()
    
@timer_func
def delay_doppler(ofdm_signal: ofdmFrame):
    ofdm_signal.delay_doppler()

for filename in os.listdir(file_folder):
    if filename.endswith(".fc32.dat"):
        for _ in range(nb_experiments):
            # Load the file
            file_path = os.path.join(file_folder, filename)
            
            # Create the frame object
            ofdm_signal = ofdmFrame(K=1024, CP=128, M=5, N=128, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=42)
            ofdm_signal.load_tysmbol_bin(file_path, type="fc32")
            
            # Measure each step of the process
            synchronization(ofdm_signal)
            demodulation(ofdm_signal)
            channel_estimation(ofdm_signal)
            equalization(ofdm_signal)
            delay_doppler(ofdm_signal)
            
            # Print the BER for verification
            ber = ofdm_signal.compute_ber()
            print(f"BER: {ber}")


# Save the results to a CSV file
df = pd.DataFrame(results, columns=["Function", "Time (ms)"])
df.to_csv("timing_results_classical.csv", index=False)
