import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.metric_calculator import metric_schmidl, metric_minn, metric_wilson, moving_sum
from rfnoc_ofdm.detector import find_max_idx

from plotting import plot_cdfs, plot_schmidl_cox


def get_sync_idx_error(ofdm_frame: ofdmFrame, threshold: float = 0.5, plot: bool = False) -> int:
    """
    Get the synchronization index from the Schmidl and Cox metric.
    """
    # Calculate P, R, M
    P_schmidl, R_schmidl, M_schmidl = metric_schmidl(ofdm_frame)
    P_minn, R_minn, M_minn = metric_minn(ofdm_frame)
    P_wilson, R_wilson, M_wilson = metric_wilson(ofdm_frame)
    
    M_schmidl = M_schmidl / np.max(M_schmidl)
    M_minn = M_minn / np.max(M_minn)
    M_wilson = M_wilson / np.max(M_wilson)
    
    # Calculate moving sum
    N_schmidl = moving_sum(M_schmidl, ofdm_frame.CP * ofdm_frame.M + 1)
    N_minn = moving_sum(M_minn, ofdm_frame.CP * ofdm_frame.M + 1)
    N_wilson = moving_sum(M_wilson, ofdm_frame.CP * ofdm_frame.M + 1)
    
    N_schmidl = N_schmidl / np.max(N_schmidl)
    N_minn = N_minn / np.max(N_minn)
    N_wilson = N_wilson / np.max(N_wilson) 
    
    # Find the detection indexes
    detection_idx_schmidl = find_max_idx(M_schmidl, threshold=threshold)
    detection_idx_schmidl_sum = find_max_idx(N_schmidl, threshold=threshold)
    detection_idx_minn = find_max_idx(M_minn, threshold=threshold)
    detection_idx_minn_sum = find_max_idx(N_minn, threshold=threshold)
    detection_idx_wilson = find_max_idx(M_wilson, threshold=threshold)
    detection_idx_wilson_sum = find_max_idx(N_wilson, threshold=threshold)
    
    # Plot the metrics
    if plot:
        plot_schmidl_cox(ofdm_frame, (M_schmidl, "Schmidl \& Cox"), threshold=threshold, sync_idx=detection_idx_schmidl, limitate=True)
        plt.savefig("schmidl_metric.pdf")
        plt.close()
        plot_schmidl_cox(ofdm_frame, (N_schmidl, "Schmidl \& Cox averaged"), threshold=threshold, sync_idx=detection_idx_schmidl_sum, info=(M_schmidl, "Schmidl"), limitate=True)
        plt.savefig("schmidl_metric_avg.pdf")
        plt.close()
        plot_schmidl_cox(ofdm_frame, (M_minn, "Minn"), threshold=threshold, sync_idx=detection_idx_minn, limitate=True)
        plt.savefig("minn_metric.pdf")
        plt.close()
        plot_schmidl_cox(ofdm_frame, (N_minn, "Minn averaged"), threshold=threshold, sync_idx=detection_idx_minn_sum, info=(M_minn, "Minn"), limitate=True)
        plt.savefig("minn_metric_avg.pdf")
        plt.close()
        plot_schmidl_cox(ofdm_frame, (M_wilson, "Wilson"), threshold=threshold, sync_idx=detection_idx_wilson, limitate=True)
        plt.savefig("wilson_metric.pdf")
        plt.close()
        plot_schmidl_cox(ofdm_frame, (N_wilson, "Wilson averaged"), threshold=threshold, sync_idx=detection_idx_wilson_sum, info=(M_wilson, "Wilson"), limitate=True)
        plt.savefig("wilson_metric_avg.pdf")
        plt.close()
    
    # Adjust the detection indexes
    # detection_idx_schmidl += (ofdm_frame.CP * ofdm_frame.M)
    # detection_idx_schmidl_sum
    # detection_idx_minn += (ofdm_frame.CP * ofdm_frame.M)
    # detection_idx_minn_sum
    # detection_idx_wilson += (ofdm_frame.CP * ofdm_frame.M)
    # detection_idx_wilson_sum
    
    true_sync_idx = ofdm_frame.preamble_tlen
    return {
        "Schmidl \& Cox": detection_idx_schmidl - true_sync_idx,
        "Minn": detection_idx_minn - true_sync_idx,
        "Wilson": detection_idx_wilson - true_sync_idx,
    }, {
        "Schmidl \& Cox averaged": detection_idx_schmidl_sum - true_sync_idx,
        "Minn averaged": detection_idx_minn_sum - true_sync_idx,
        "Wilson averaged": detection_idx_wilson_sum - true_sync_idx,
    }


#####################################################
# CDF of Sync Index Error over multiple experiments #
#####################################################
n_exp = 2000
metric_results = []
metric_avg_results = []
for _ in tqdm.tqdm(range(n_exp), desc="Simulating OFDM frames"):
    ofdm_frame = ofdmFrame(K=64, CP=16, M=4, N=4, preamble_mod="BPSK", payload_mod="QPSK", Nt=3, Nf=1)
    ofdm_frame.add_paths([1, 0.25], [0, 2], 10)
    
    # Get the sync index error
    sync_idx, sync_idx_avg = get_sync_idx_error(ofdm_frame, threshold=0.5)
    metric_results.append(sync_idx)
    metric_avg_results.append(sync_idx_avg)
df_results = pd.DataFrame(metric_results)
df_avg_results = pd.DataFrame(metric_avg_results)  

# Plot both dataframes
plot_cdfs(df_results, ofdm_frame, False, title="CDF of Sync Index Error on metrics")
plt.savefig("sync_index_error_metrics.pdf")
plot_cdfs(df_avg_results, ofdm_frame, True, title="CDF of Sync Index Error on averaged metrics averaged")
plt.savefig("sync_index_error_metrics_avg.pdf")


##############################################
# Plot the different metrics on a same frame #
##############################################
ofdm_frame = ofdmFrame(K=64, CP=16, M=4, N=4, preamble_mod="BPSK", payload_mod="QPSK", Nt=3, Nf=1)
ofdm_frame.add_paths([1, 0.25], [0, 2], 10)
_, _ = get_sync_idx_error(ofdm_frame, threshold=0.5, plot=True)
