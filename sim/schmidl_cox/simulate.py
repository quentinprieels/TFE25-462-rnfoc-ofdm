import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame

from metric_calculator import *
from detector import *
from plotting import plot_schmidl_cox

ofdm_frame = ofdmFrame(K=1024, CP=128, M=1, N=2, preamble_mod="BPSK", payload_mod="QPSK", Nt=2, Nf=1024, random_seed=42)
ofdm_frame.add_noise(10)
P, R, M = metric_schmidl(ofdm_frame)
N = moving_sum(M, ofdm_frame.CP)

# Normalize the metric
P = P / np.max(np.abs(P))
R = R / np.max(np.abs(R))
M = M / np.max(np.abs(M))
N = N / np.max(np.abs(N))

# Find the detection index
detection_idx = find_max_idx(N, threshold=0.5)

# Plot the metrics
plot_schmidl_cox(ofdm_frame, (N, "N"), info=(M, 'M'), threshold=0.5, limitate=True, sync_idx=detection_idx)
plt.show()