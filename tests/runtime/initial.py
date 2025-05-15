import os
from timeit import default_timer as timer
import pandas as pd

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

folder = "../../data/long_raw.signal"
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
def synchronization(ofdm_frame: ofdmFrame):
    sync_idx = ofdm_frame.get_frame_synchronization_idx()
    sync_idx = sync_idx + ofdm_frame.preamble_tlen - (ofdm_frame.CP // 2 * ofdm_frame.M)
    ofdm_frame.tsymbols_rx = ofdm_frame.tsymbols_rx[sync_idx:]
    
def synchronization_utils(ofdm_frame: ofdmFrame):
    @timer_func
    def synchronization_util(ofdm_frame: ofdmFrame):
        ofdm_frame.get_frame_synchronization_idx()
    
    # Measure only the time of "True detection"
    sync_idx = ofdm_frame.get_frame_synchronization_idx()
    sync_idx = sync_idx + ofdm_frame.preamble_tlen - (ofdm_frame.CP // 2 * ofdm_frame.M)
    
    # Make a copy of the frame for re-synchronization measurement
    ofdm_frame_cpy = ofdmFrame(K=1024, CP=128, M=4, N=256, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=42)
    received_preamble = ofdm_frame.tsymbols_rx.copy()[sync_idx:sync_idx+ofdm_frame_cpy.preamble_tlen]
    ofdm_frame_cpy.tsymbols_rx = received_preamble
    synchronization_util(ofdm_frame_cpy)
    # End of re-synchronization measurement
    
    ofdm_frame.tsymbols_rx = ofdm_frame.tsymbols_rx[sync_idx:]
    
@timer_func
def demodulation(ofdm_frame: ofdmFrame):
    ofdm_frame.demodulate_frame()

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
            synchronization(ofdm_signal)
            synchronization_utils(ofdm_signal) # For util-measurement comparison
            demodulation(ofdm_signal)
            channel_estimation(ofdm_signal)
            equalization(ofdm_signal)
            delay_doppler(ofdm_signal)
            

# Save results to CSV
df = pd.DataFrame(results, columns=['Function', 'Time (ms)'])
df.to_csv("timing_results_initial_util.csv", index=False)
