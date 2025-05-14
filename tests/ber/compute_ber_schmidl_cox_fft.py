"""
Compute the Bit Error Rate (BER) of a folder of measurements, where the signal
corresponds to the OFDM payload already passed through the FFT (operations performed in hardware).
"""
# Imports
import os
import pandas as pd

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

# Target folder
folder = "../../data/long_schmidl_cox_fft.signal"
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
def compute_ber_schmidl_cox_fft(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed):
    bers = {}
    for filename in os.listdir(folder):
        if not filename.endswith(".dat"):
            continue       
        # Create the frame pilots and load received data
        ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
        ofdm_frame.load_tysmbol_bin(folder + "/" + filename)
        
        # Demodulation
        ofdm_frame.reshape_after_hardware_fft()
        
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
    df.to_csv(folder + "/ber_results.csv", index=False)
    df.to_csv("ber_results_schmidl_cox_fft.csv", index=False)
  
    
compute_ber_schmidl_cox_fft(folder, K, CP, M, N, preamble_mod, payload_mod, Nt, Nf, random_seed)
