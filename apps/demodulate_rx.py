import hashlib
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import plot_constellation

# Signal parameters
K = 1024                # Number of subcarriers
CP = 128                # Length of the cyclic prefix
M = 5                   # Oversampling factor
N = 256                 # Number of OFDM symbols
preamble_mod = "BPSK"   # Preamble modulation
payload_mod = "QPSK"    # Payload modulation
Nt = 4                  # Time domain pilot spacing
Nf = 1                  # Frequency domain pilot spacing
random_seed = 42        # Random seed for reproducibility => THIS MUST BE THE SAME AS IN THE `create_tx.py` FILE!

filename = "../tests/rx_samples_schmidl_cox.signal.fc32.dat"  # File to load the received signal

# Create the signal
ofdm_signal = ofdmFrame(K=K, CP=CP, M=M, N=N, preamble_mod=preamble_mod, payload_mod=payload_mod, Nt=Nt, Nf=Nf, random_seed=random_seed)
ofdm_signal.load_tysmbol_bin(filename, type="fc32")
ofdm_signal.demodulate_frame()
ofdm_signal.equalize()
plot_constellation(ofdm_signal)
plt.savefig("../tests/constellation.pdf")

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
print()

data = ofdm_signal.tsymbols.tobytes()
digest = hashlib.sha256(data).hexdigest()[:12]
print(f"Generated signal hash: {digest}")

print(f"BER: {ofdm_signal.compute_ber()}")

# TX COMMAND: ./tx_waveforms_radar --args name=sam subdev "A:0" --ant "TX/RX" --rate 200e6 --freq 3.2e9 --sig_len 29952 --spb 59904 --file "OFDM_frame_1024_128_1_25_BPSK_QPSK.txt" --gain 30 --ref "external"
# RX COMMAND: ./rx_to_file --nsamps 59904 --datapath raw --format sc16