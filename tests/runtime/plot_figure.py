import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib as mpl

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure pyfunctionthon find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import colors, classical, use_latex
from rfnoc_ofdm.metric_calculator import metric_schmidl, moving_sum
from rfnoc_ofdm.detector import find_max_idx

results_file = "timing_results_initial.csv"


# Assuming `results_poster.csv` is properly formatted and present
results = pd.read_csv(results_file)
print(results.head())

# Group by function and take the mean of the time and the standard deviation
results = results.groupby(['Function']).agg({'Time (ms)': ['mean', 'std']}).reset_index()
print(results)

# Compute the total common time (addition of the mean times of the (synchronization, demodulation, and channel estimation) functions)
# Extract the mean times for synchronization, demodulation, and channel estimation
sync_time = results.loc[results['Function'] == 'synchronization', ('Time (ms)', 'mean')].values[0]
demod_time = results.loc[results['Function'] == 'demodulation', ('Time (ms)', 'mean')].values[0]
channel_est_time = results.loc[results['Function'] == 'channel_estimation', ('Time (ms)', 'mean')].values[0]

# Compute the total common time by adding them together
common_time = sync_time + demod_time + channel_est_time
print(f"Total common time: {common_time} ms")

# Color for each block
block_colors = {
    "synchronization": colors["line1"],
    "demodulation": colors["line2"],
    "channel_estimation": colors["line3"],
    "equalization": colors["line4"],
    "delay_doppler": colors["line5"],
    "common": "white"
}

x = ["Communication", "Common", "RADAR" ]

# Bar 1 is "Synchornization", "common", "common"
bar1 = [
    common_time,
    results.loc[results['Function'] == 'synchronization', 'Time (ms)'].values[0],
    common_time
]
bar1_colors = [
    block_colors["common"],
    block_colors["synchronization"],
    block_colors["common"],
]
bar1_hatch = [
    "/ /",
    "",
    "/ /",
]
# Bar 2 is "OFDM_demodulation", "OFDM_channel_equalisation", "new_SISO_OFDM_DFRC_RADAR_RX"
# Bar 2 is "demodulation", "equalization", "delay_doppler"
bar2 = [
    results.loc[results['Function'] == 'equalization', 'Time (ms)'].values[0],
    results.loc[results['Function'] == 'demodulation', 'Time (ms)'].values[0],
    results.loc[results['Function'] == 'delay_doppler', 'Time (ms)'].values[0]    
]
bar2_colors = [
    block_colors["equalization"],
    block_colors["demodulation"],
    block_colors["delay_doppler"],
]


# Bar 3 is "channel_estimation", "0", "0"
bar3 = [
    0,
    results.loc[results['Function'] == 'channel_estimation', 'Time (ms)'].values[0],
    0
]
bar3_colors = [
    "none",  # No color since the value is 0
    block_colors["channel_estimation"],
    "none",  # No color since the value is 0
]

# use the Montserrat-Medium font for the plot (.ttf file in the same directory)
font = FontProperties(fname='Montserrat-Medium.ttf')
font.set_size(14)
mpl.rcParams['hatch.linewidth'] = 0.8  # Adjust as needed


# Figure parameters
bin_height = 0.8

# reduce the margins

plt.figure(figsize=(12, 2.5))  # Reduced height
plt.barh(x, bar1, color=bar1_colors, hatch=bar1_hatch, height=bin_height)
plt.barh(x, bar2, left=bar1, color=bar2_colors, height=bin_height)
plt.barh(x, bar3, left=np.add(bar1, bar2), color=bar3_colors, height=bin_height)

plt.xlabel('Time [ms]', fontproperties=font)
#plt.ylabel('Chain', fontproperties=font)
plt.xticks(fontproperties=font)
plt.yticks(fontproperties=font)
plt.subplots_adjust(bottom=0.2)  # Adjust bottom margin
plt.subplots_adjust(left=0.15)  # Adjust left margin

#plt.savefig('complexity.pdf', bbox_inches='tight', pad_inches=0)
# plt.legend()
plt.show()