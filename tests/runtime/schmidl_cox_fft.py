import os
from timeit import default_timer as timer
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

folder = "../../data/long_schmidl_cox_fft.signal"
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


@timer_func
def demodulation(ofdm_frame: ofdmFrame):
    ofdm_frame.reshape_after_hardware_fft()

@timer_func  
def channel_estimation(ofdm_frame: ofdmFrame):
    ofdm_frame.estimate_channel()

@timer_func
def equalization(ofdm_frame: ofdmFrame):
    ofdm_frame.equalize()
    
@timer_func
def delay_doppler(ofdm_frame: ofdmFrame):
    ofdm_frame.delay_doppler()
    

# Experiment loop
for filename in os.listdir(folder):
    if filename.endswith(".fc32.dat"):
        for _ in range(nb_experiments):
            # Load the file
            file_path = os.path.join(folder, filename)
            
            # Create the frame object
            ofdm_signal = ofdmFrame(K=1024, CP=128, M=4, N=256, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=42)
            ofdm_signal.load_tysmbol_bin(file_path, type="fc32")
            
            # Measure each step of the process
            demodulation(ofdm_signal)
            channel_estimation(ofdm_signal)
            equalization(ofdm_signal)
            delay_doppler(ofdm_signal)
            

# Save results to CSV
df = pd.DataFrame(results, columns=['Function', 'Time (ms)'])
df.to_csv("timing_results_schmidl_cox_fft.csv", index=False)
