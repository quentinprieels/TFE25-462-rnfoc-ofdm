import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

#################
# Data 4 folder #
#################
folder = "data_4"
K = 1024
CP = 128
M = 5
N = 4
preamble_mod = "BPSK"
payload_mod = "QPSK"
Nt = 3
Nf = 1
random_seed = 42

bers = {}
for filename in os.listdir(folder):
    if not filename.endswith(".dat"):
        continue
    ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
    ofdm_frame.load_tysmbol_bin(folder + "/" + filename)
    ofdm_frame.demodulate_frame()
    ofdm_frame.equalize()
    ber = ofdm_frame.compute_ber()
    bers[filename] = ber
    
df = pd.DataFrame.from_dict(bers, orient='index', columns=['BER'])
df.index.name = 'Filename'
df.reset_index(inplace=True)
df['meas_num'] = df['Filename'].str.extract(r'meas(\d+)')[0].astype(int)
df.sort_values(by='meas_num', inplace=True)
df.drop(columns=['meas_num'], inplace=True)
df.to_csv(folder + "/ber_results.csv", index=False)


###################
# Data 256 folder #
###################
folder = "data_256"
K = 1024
CP = 128
M = 5
N = 256
preamble_mod = "BPSK"
payload_mod = "QPSK"
Nt = 4
Nf = 1
random_seed = 42

bers = {}
for filename in os.listdir(folder):
    if not filename.endswith(".dat"):
        continue
    ofdm_frame = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
    ofdm_frame.load_tysmbol_bin(folder + "/" + filename)
    ofdm_frame.demodulate_frame()
    ofdm_frame.equalize()
    ber = ofdm_frame.compute_ber()
    bers[filename] = ber
    
df = pd.DataFrame.from_dict(bers, orient='index', columns=['BER'])
df.index.name = 'Filename'
df.reset_index(inplace=True)
df['meas_num'] = df['Filename'].str.extract(r'_meas(\d+).')[0].astype(int)
df.sort_values(by='meas_num', inplace=True)
df.drop(columns=['meas_num'], inplace=True)
df.to_csv(folder + "/ber_results.csv", index=False)