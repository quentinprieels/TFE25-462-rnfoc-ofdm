import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure python find the rfnoc_ofdm package
from rfnoc_ofdm.ofdm_frame import ofdmFrame
from rfnoc_ofdm.plotting import plot_frame_waveform, colors


def plot_schmidl_cox(ofdm_frame: ofdmFrame, metric: tuple[np.ndarray, str], threshold: float, sync_idx: int = None,
                     info: tuple[np.ndarray, str] = None, other_subtitles: dict = None, use_rx_symbols: bool = True,
                     limitate: bool = False, view_title: bool = True) -> None:
    
    line_annotation_height = 1.1
    line2_annotation_height = 1.025
    text_annotation_height = 1.12
    
    # Annotated frame
    plot_frame_waveform(ofdm_frame, view_title=False, use_rx=True)
    
    # CP copied
    cp_copied_preamble_start = ofdm_frame.K * ofdm_frame.M
    cp_copied_preamble_end = (ofdm_frame.CP + ofdm_frame.K) * ofdm_frame.M
    plt.text(cp_copied_preamble_start + (cp_copied_preamble_end - cp_copied_preamble_start) // 2, 0.93 * text_annotation_height, "CP cpy", horizontalalignment='center', clip_on=True, color=colors["orange"])
    plt.annotate("", xy=(cp_copied_preamble_end, line2_annotation_height), xytext=(cp_copied_preamble_start, line2_annotation_height), arrowprops=dict(arrowstyle="<->", color=colors["orange"]), clip_on=True)
    plt.vlines(x=cp_copied_preamble_start, ymax=line_annotation_height, linestyles='-.', color=colors["orange"], ymin=0)

    # Title and subtitle
    title = "Schmidl and Cox Synchronization Algorithm"    
    subtitle_info = {
        "K": f"{ofdm_frame.K:}",
        "CP": f"{ofdm_frame.CP:}",
        "M": f"{ofdm_frame.M:}",
        "Preamble modulation": ofdm_frame.preamble_mod,
        "Payload modulation":  ofdm_frame.payload_mod,
    }
    subtitle = f"{' - '.join(sorted([f'{k}: {v}' for k, v in subtitle_info.items()]))}"
    if other_subtitles is not None:
        subtitle += f"\n{' - '.join([f'{k}: {v}' for k, v in other_subtitles.items()])}"
    
    if view_title:
        plt.suptitle(title, fontsize=14, fontweight="bold")
        plt.title(subtitle, fontsize=10, fontstyle="italic")
    
    plt.twinx()
    
    # Metric
    plt.plot(metric[0], color='red', label=metric[1])
    if info is not None:
        plt.plot(info[0], color='red', label=info[1], linestyle='--')
        
    plt.axhline(y=threshold, color='tab:brown', linestyle=':', label="Threshold")
    
    if sync_idx is not None:
        plt.axvline(x=sync_idx, color='tab:green', linestyle='-.', label="Sync index")
    
    # Detection zone
    above_threshold = metric[0] > threshold
    crossing_points = np.where(np.diff(above_threshold.astype(int)))[0][:2]
    if len(crossing_points) == 2: 
        plt.axvspan(crossing_points[0], crossing_points[1], color='gray', alpha=0.2, hatch='//')
    
    if limitate:
        payload_start = (ofdm_frame.K + ofdm_frame.CP) * ofdm_frame.M
        payload_end = 1.75 * (ofdm_frame.K + ofdm_frame.CP) * ofdm_frame.M
        plt.text(payload_start + (payload_end - payload_start) // 2, text_annotation_height, "Payload", horizontalalignment='center', clip_on=True)
        plt.annotate("", xy=(payload_end, line_annotation_height), xytext=(payload_start, line_annotation_height), arrowprops=dict(arrowstyle="<-"), clip_on=True)
        plt.xlim(0, payload_end)   
    
    plt.ylim(0, 1.2)
    plt.legend(loc="lower right")
    plt.ylabel("Metrics M[n]")
    plt.tight_layout()
    
    
# Function to plot CDF
def plot_cdfs(df: pd.DataFrame, ofdm_frame: ofdmFrame, title: str = "", view_title: bool = False) -> None:
    plt.figure(figsize=(8, 6))
    if view_title:
        plt.suptitle(title, fontsize=14, fontweight="bold")
    
    line_styles = ['-', '--', '-.', ':', '-', '--', '-.']
    all_min = df.min().min()
    all_max = df.max().max()
    
    for column in df.columns:
        column_data = np.sort(df[column].values)
        y_values = np.arange(1, len(column_data) + 1) / len(column_data) * 100
        
        # Create extended x and y arrays
        x_extended = []
        y_extended = []
        
        # Add minimum point if needed
        if column_data[0] > all_min:
            x_extended.append(all_min)
            y_extended.append(0)
        
        # Add the actual data points
        for i, val in enumerate(column_data):
            x_extended.append(val)
            y_extended.append(y_values[i])
        
        # Add the maximum point if needed
        if column_data[-1] < all_max:
            x_extended.append(all_max)
            y_extended.append(100)        
        
        col_idx = list(df.columns).index(column)
        plt.plot(x_extended, y_extended, 
             linestyle=line_styles[col_idx % len(line_styles)], 
             linewidth=2, 
             label=column)
    
    # Add the gray area of successful detection
    cp_size = ofdm_frame.CP * ofdm_frame.M
    plt.axvspan(-cp_size // 2, cp_size // 2, color='gray', alpha=0.2, hatch='//')
    
    plt.xlabel('Error Value [index]')
    plt.ylabel('Cumulative Percentage [%]')
    plt.grid(linestyle='--')
    plt.legend()
    plt.tight_layout()


if __name__ == "__main__":
    from metric_calculator import metric_schmidl, moving_sum
    from detector import find_max_idx
    
    # Plot example of the Schmidl and Cox metric
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
    plot_schmidl_cox(ofdm_frame, (N, "N"), info=(M, 'M'), threshold=0.5, limitate=True, sync_idx=detection_idx, view_title=False)
    plt.savefig("schmidl_cox.pdf")
