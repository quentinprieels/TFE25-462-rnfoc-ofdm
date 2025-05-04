import hashlib
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import *

# Signal parameters
K = 1024                # Number of subcarriers
CP = 128                # Length of the cyclic prefix
M = 5                   # Oversampling factor
N = 256                 # Number of OFDM symbols
preamble_mod = "BPSK"   # Preamble modulation
payload_mod = "QPSK"    # Payload modulation
Nt = 4                  # Time domain pilot spacing
Nf = 1                  # Frequency domain pilot spacing
random_seed = 42        # Random seed for reproducibility
threshold = 10485760    # Threshold for the Schmidl-Cox algorithm => found by testbench over the raw data


# Create the signal
ofdm_signal = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
filename = ofdm_signal.save_tsymbols_txt(auto_filename=True)

# Print useful information necessary to run the receiver `rx_to_file` program
print(f"Signal parameters:")
print(f"  K: {K}")
print(f"  CP: {CP}")
print(f"  M: {M}")
print(f"  N: {N}")
print(f"  preamble_mod: {preamble_mod}")
print(f"  payload_mod: {payload_mod}")
print(f"  Nt: {Nt}")
print(f"  Nf: {Nf}")
print(f"  Random seed: {random_seed}")
print(f"  Signal filename: {filename}\n")


print(f"Number of data samples to receive (N * (K + CP) * M) - nsamp: {N * (K + CP) * M}")
print(f"Number of samples to transmit ((N+1) * (K + CP) * M) - sig_len: {(N + 1) * (K + CP) * M}")
print(f"Buffer size for the transmitter - 2*sig_len: {2 * (N + 1) * (K + CP) * M}\n")

data = ofdm_signal.tsymbols.tobytes()
digest = hashlib.sha256(data).hexdigest()[:12]
print(f"Generated signal hash: {digest}\n")

print(f"TX COMMAND: ./tx_waveforms_radar --args name=sam subdev \"A:0\" --ant \"TX/RX\" --rate 200e6 --freq 3.2e9 --sig_len {(N + 1) * (K + CP) * M} --spb {2 * (N + 1) * (K + CP) * M} --file \"{filename}\" --gain 30 --ref \"external\"")
print(f"RX COMMAND RAW: ./rx_to_file --nsamps {2 * (N + 1) * (K + CP) * M} --datapath raw --format sc16")
print(f"RX COMMAND SCHMIDL COX: ./rx_to_file --nsamps {2 * (N + 1) * (K + CP) * M} --datapath schmidl_cox --format fc32 --sc_packet_size {N * (K + CP) * M} --sc_output_select 1 --sc_threshold {threshold}\n")
