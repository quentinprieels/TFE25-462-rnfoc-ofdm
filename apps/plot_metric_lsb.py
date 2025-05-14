import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.plotting import colors, classical, use_latex

filename = "../data/mean_all.all/rx_samples_schmidl_cox.metricLSB.int32.dat"

signal = np.fromfile(filename, dtype=np.int32)
threshold = 10485760

# Plot the signal
plt.figure(figsize=classical)
use_latex()
plt.plot(signal, color=colors["metric"], label="Metric LSB")
plt.axhline(y=threshold, color=colors["threshold"], linestyle="-.", label="Threshold")
plt.xlabel("Sample index [d]")
plt.ylabel("Metric LSB from FPGA $N[d]$")
plt.grid(linestyle="--")
plt.tight_layout()
plt.savefig("../data/mean_all.all/rx_samples_schmidl_cox.metricLSB.int32.pdf")

plt.figure(figsize=classical)
use_latex()
plt.plot(signal, color=colors["metric"], label="Metric LSB")
plt.axhline(y=threshold, color=colors["threshold"], linestyle="-.", label="Threshold")
plt.xlim(10000, 20000)
plt.xlabel("Sample index [d]")
plt.ylabel("Metric LSB from FPGA $N[d]$")
plt.grid(linestyle="--")
plt.tight_layout()
plt.savefig("../data/mean_all.all/rx_samples_schmidl_cox.metricLSB_zoomed.int32.pdf")