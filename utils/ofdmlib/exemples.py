import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import plot_frame_matrix, plot_frame_waveform, plot_constellation, plot_ber_vs_snr


# Plot the frame matrix
ofdm_frame = ofdmFrame(K=32, CP=8, M=5, N=25, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=0)
plot_frame_matrix(ofdm_frame, view_bits=True, view_title=False)
plt.savefig("frame_matrix.pdf", bbox_inches="tight")


# Plot the frame waveform
ofdm_frame = ofdmFrame(K=1024, CP=256, M=5, N=5, preamble_mod="BPSK", payload_mod="QPSK", Nt=4, Nf=1, random_seed=0)
plot_frame_waveform(ofdm_frame, view_title=False)
plt.savefig("frame_waveform.pdf", bbox_inches="tight")


# Save the time domain symbols to a file
ofdm_frame = ofdmFrame(K=1024, CP=128, M=1, N=3, preamble_mod="BPSK", payload_mod="QPSK", Nt=3, Nf=1, random_seed=0)
ofdm_frame.save_tsymbols_txt(auto_filename=True)


# Save the time domain symbols to a file
ofdm_frame = ofdmFrame(K=1024, CP=128, M=1, N=3, preamble_mod="BPSK", payload_mod="QPSK", Nt=3, Nf=1, random_seed=0)
ofdm_frame.add_noise(10)
ofdm_frame.demodulate_frame(remove_first_symbol=True)
ofdm_frame.equalize()
plot_constellation(ofdm_frame, view_title=False)
plt.savefig("constellation.pdf", bbox_inches="tight")

         
# Plot the BER vs SNR curve for each payload modulation scheme
snrs = np.arange(-10, 20, 2)
mods = ["BPSK", "QPSK"]
n_exp = 20
random_seeds = np.arange(n_exp)
results_list = []

for mod in mods:
    for snr in snrs:
        for i in range(n_exp):
            ofdm_frame = ofdmFrame(K=1024, CP=0, M=1, N=250, preamble_mod="BPSK", payload_mod=mod, Nt=250, Nf=1024, random_seed=random_seeds[i])
            ofdm_frame.add_noise(snr)
            ofdm_frame.demodulate_frame(remove_first_symbol=True, CP_rx=False)
            ofdm_frame.equalize()
            ber = ofdm_frame.compute_ber()
            results_list.append({"SNR": snr, "Modulation": mod, "BER": ber})

ber_results = pd.DataFrame(results_list)
plot_ber_vs_snr(ber_results, view_title=False, params={"K": 1024, "CP": 0, "M": 1, "N": 250, "Nt": 250, "Nf": 1024})
plt.savefig("ber_vs_snr.pdf", bbox_inches="tight")
