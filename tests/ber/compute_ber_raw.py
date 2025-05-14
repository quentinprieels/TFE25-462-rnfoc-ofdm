"""
Compute the Bit Error Rate (BER) of a folder of measurements, where the signal
corresponds to the OFDM payload only (the Schmidl-Cox preamble must be removed by the hardware).
"""
# Imports
import os
import pandas as pd
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.metric_calculator import metric_schmidl, moving_sum
from rfnoc_ofdm.detector import find_max_idx

# Target folder
folder = "../../data/long_raw.signal"
K = 1024
CP = 128
M = 4
N = 256
preamble_mod = "BPSK"
payload_mod = "QPSK"
Nt = 4
Nf = 1
random_seed = 42

# Demodulation chain in post-processing
def compute_ber_raw_schmidl_cox(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed):
    bers = {}
    for filename in os.listdir(folder):
        if not filename.endswith(".dat"):
            continue
        
        # Create the frame pilots and load received data
        ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
        ofdm_frame.load_tysmbol_bin(folder + "/" + filename)
        
        # Synchronization
        P_schmidl, R_schmidl, M_schmidl = metric_schmidl(ofdm_frame)
        N_schmidl = moving_sum(M_schmidl, ofdm_frame.CP * ofdm_frame.M)
        sync_idx = find_max_idx(N_schmidl, 300)  - (ofdm_frame.CP // 2 * ofdm_frame.M)           
        ofdm_frame.tsymbols_rx = ofdm_frame.tsymbols_rx[sync_idx:]        
        
        # Demodulation
        ofdm_frame.demodulate_frame()
        
        # Channel estimation
        ofdm_frame.estimate_channel()
        
        # Equalization
        ofdm_frame.equalize()
        
        # Compute BER
        ber = ofdm_frame.compute_ber()
        bers[filename] = ber
        
    df = pd.DataFrame.from_dict(bers, orient='index', columns=['BER'])
    df.index.name = 'Filename'
    df.reset_index(inplace=True)
    df['meas_num'] = df['Filename'].str.extract(r'meas(\d+)')[0].astype(int)
    df.sort_values(by='meas_num', inplace=True)
    df.drop(columns=['meas_num'], inplace=True)
    df.to_csv(folder + "/ber_results_schmidl_cox.csv", index=False)
    df.to_csv("ber_results_raw_schmidl_cox.csv", index=False)

def compute_ber_raw_correlation(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed):
    bers = {}
    for filename in os.listdir(folder):
        if not filename.endswith(".dat"):
            continue
        
        # Create the frame pilots and load received data
        ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
        ofdm_frame.load_tysmbol_bin(folder + "/" + filename)
        
        # Synchronization
        sync_idx = ofdm_frame.get_frame_synchronization_idx()
        sync_idx = sync_idx + ofdm_frame.preamble_tlen - (ofdm_frame.CP // 2 * ofdm_frame.M)
        ofdm_frame.tsymbols_rx = ofdm_frame.tsymbols_rx[sync_idx:]
        
        # Demodulation
        ofdm_frame.demodulate_frame()
        
        # Channel estimation
        ofdm_frame.estimate_channel()
        
        # Equalization
        ofdm_frame.equalize()
        
        # Compute BER
        ber = ofdm_frame.compute_ber()
        bers[filename] = ber
        
    df = pd.DataFrame.from_dict(bers, orient='index', columns=['BER'])
    df.index.name = 'Filename'
    df.reset_index(inplace=True)
    df['meas_num'] = df['Filename'].str.extract(r'meas(\d+)')[0].astype(int)
    df.sort_values(by='meas_num', inplace=True)
    df.drop(columns=['meas_num'], inplace=True)
    df.to_csv(folder + "/ber_results_correlation.csv", index=False)
    df.to_csv("ber_results_raw_correlation.csv", index=False)
  
    
compute_ber_raw_schmidl_cox(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed)
compute_ber_raw_correlation(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed)
