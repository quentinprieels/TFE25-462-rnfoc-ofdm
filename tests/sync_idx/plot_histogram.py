import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import colors, classical, use_latex
from rfnoc_ofdm.metric_calculator import metric_schmidl, moving_sum
from rfnoc_ofdm.detector import find_max_idx

data = pd.read_csv("sync_idx_errors_results.csv")
# Plot the histogram of the errors
plt.figure(figsize=classical)
#use_latex()
plt.hist(data["Index Error"], bins=10, color=colors["line1"])
plt.xlabel("Error (# samples)")
plt.ylabel("Frequency")
plt.title("Histogram of Synchronization Errors")
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()