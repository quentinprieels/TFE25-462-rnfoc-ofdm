import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import plot_frame_waveform

filename = "rx_samples_schmidl_cox.signal.fc32.dat"
ofdm_signal = ofdmFrame(K=1024, CP=128, M=5, N=128, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=42)

ofdm_signal.load_tysmbol_bin(filename, type="fc32")

# Demodulation
ofdm_signal.demodulate_frame()

# Channel estimation
ofdm_signal.estimate_channel()

# Equalization
ofdm_signal.equalize()

# Print BER
print(f"BER: {ofdm_signal.compute_ber()}")
