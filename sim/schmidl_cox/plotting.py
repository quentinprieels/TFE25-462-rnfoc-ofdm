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
    