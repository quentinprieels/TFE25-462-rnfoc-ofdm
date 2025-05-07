from cycler import cycler
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.special import erfc

from .ofdm_frame import ofdmFrame

# Color palette
blue_drak = "#00204e"
blue_light = "#9cb7d4"
blue_bright = "#5bd4e6"
purple = "#8b687f"
yellow = "#E9AE49"
green = "#8EC87E"
red = "#F16A6A"

colors = {    
    # Colors
    "blue_dark": blue_drak,
    "blue_light": blue_light,
    "blue_bright": blue_bright,
    "purple": purple,
    "yellow": yellow,
    "green": green,
    "red": red,
    
    # Received signal
    "preamble": blue_drak,
    "pilot": blue_bright,
    "signal": blue_light,
    
    # Send vs received
    "send": purple,
    "received": blue_light,
    
    # Signal / metric
    "metric": red,
    "threshold": yellow,
    "sync": green,
    "CP": purple,
    "info": blue_drak,
    
    # Mutliple lines
    "line1": blue_drak,
    "line2": purple,
    "line3": green,
    "line4": red,
    "line5": yellow,
    "line6": blue_bright,
}

# Size
square = (5, 5)
classical = (10, 6)
long = (15, 5)

# Set the default matplotlib parameters
plt.rcParams['axes.prop_cycle'] = cycler(color=list(colors.values()))
plt.rcParams['font.family'] = 'sans-serif'

def plot_frame_matrix(ofdm_frame: ofdmFrame, view_bits: bool = False, view_title: bool = True) -> None:
    """
    Plot the pilot matrix: the signal in a (time x subcarrier) matrix.
    """
    pilots_idx_t_mesh, pilots_idx_f_mesh = ofdm_frame.get_pilots_grid()
    
    # Create the matrix of symbol types
    matrix = np.zeros((1 + ofdm_frame.N, ofdm_frame.K))  # (1 + N) x K matrix
    matrix[0, :] = 2  # Timing synchronization preamble
    matrix[pilots_idx_t_mesh.T + 1, pilots_idx_f_mesh.T] = 1  # Pilots
    
    # Create the matrix of bits sent
    bits_per_symbol = ofdm_frame._bits_per_fsymbol[ofdm_frame.payload_mod]
    bits_matrix = np.zeros((1 + ofdm_frame.N, ofdm_frame.K * bits_per_symbol), dtype=int)
    bits_matrix[1:, :] = ofdm_frame.bits_payload
    
    # Reshape and convert to binary format
    bits_matrix = bits_matrix.reshape((1 + ofdm_frame.N, ofdm_frame.K, bits_per_symbol))
    binary_matrix = np.array([
        ["".join(map(str, bits_matrix[i, j])) for j in range(ofdm_frame.K)]
        for i in range(1 + ofdm_frame.N)
    ])
    
    binary_matrix[0, :] = ""  # Preamble has no bits
    
    # Plot
    data_legend_idx = 0 + (2 / 3) / 2
    pilot_legend_idx = 1
    preamble_legend_idx = 2 - (2 / 3) / 2
    
    plt.figure("OFDM frame matrix", figsize=classical)
    
    if view_title:
        plt.suptitle("OFDM frame matrix", fontsize=14, fontweight="bold")
        plt.title(f"Parameters: K={ofdm_frame.K}, N={ofdm_frame.N}, Nt={ofdm_frame.Nt}, Nf={ofdm_frame.Nf}", fontsize=10, fontstyle="italic")
    
    sns.heatmap(matrix,
                cmap=sns.color_palette([colors["signal"], colors["pilot"], colors["preamble"]]),
                cbar_kws={"ticks": [0, 1, 2], "format": "%d"},
                linewidths=0.5,
                linecolor="black",
                alpha=0.5,
                annot=binary_matrix if view_bits else None,
                fmt="",
                annot_kws={"color": "black"})
    colorbar = plt.gca().collections[0].colorbar
    colorbar.set_ticks([data_legend_idx, pilot_legend_idx, preamble_legend_idx])
    colorbar.set_ticklabels(["Data", "Pilots", "Preamble"])
    plt.ylabel("OFDM symbols (time)")
    plt.xlabel("Subcarriers (frequency)")
    plt.tight_layout()

def plot_frame_waveform(ofdm_frame: ofdmFrame, use_rx: bool = False, view_title: bool = True, params_for_title: dict = None, symbol_annoation: bool = True) -> None:
    """
    Plot the time domain waveform of the OFDM frame.
    """
    plt.figure("OFDM Frame", figsize=long)
        
    # Title and subtitle
    title = "OFDM Frame"
    subtitle_params_values = {
        "K": f"{ofdm_frame.K:}",
        "CP": f"{ofdm_frame.CP:}",
        "M": f"{ofdm_frame.M:}",
        "Preamble modulation": ofdm_frame.preamble_mod,
        "Payload modulation": ofdm_frame.payload_mod
    }
    if params_for_title is not None:
        for key, value in params_for_title.items():
            if key not in subtitle_params_values:
                subtitle_params_values[key] = value
    subtitle = f"Parameters: {' - '.join(sorted([f'{k}: {v}' for k, v in subtitle_params_values.items()]))}"
    
    if view_title:
        plt.suptitle(title, fontsize=14, fontweight="bold")
        plt.title(subtitle, fontsize=10, fontstyle="italic")
    
    line_annotation_height = 1.1
    line2_annotation_height = 1.025
    text_annotation_height = 1.12
        
    # Signal plot

    normalized_frame = np.abs(ofdm_frame.tsymbols) / np.max(np.abs(ofdm_frame.tsymbols))
    if use_rx:
        normalized_frame = np.abs(ofdm_frame.tsymbols_rx) / np.max(np.abs(ofdm_frame.tsymbols_rx))
    plt.plot(normalized_frame, label="OFDM frame", color=colors["signal"], alpha=0.6)
    
    # Signal information (sto, cp, ...)
    preamble_start = 0
    payload_start = (ofdm_frame.CP + ofdm_frame.K) * ofdm_frame.M
    payload_end = payload_start + ofdm_frame.N * (ofdm_frame.CP + ofdm_frame.K) * ofdm_frame.M
    
    assert payload_end == len(normalized_frame), "The frame length is not correct"
    
    # Global frame information
    plt.text(preamble_start + payload_start // 2, text_annotation_height, "Preamble", horizontalalignment='center', clip_on=True)
    plt.annotate("", xy=(payload_start, line_annotation_height), xytext=(preamble_start, line_annotation_height), arrowprops=dict(arrowstyle="<->"), clip_on=True)

    plt.text(payload_start + (payload_end - payload_start) // 2, text_annotation_height, "Payload", horizontalalignment='center', clip_on=True)
    plt.annotate("", xy=(payload_end, line_annotation_height), xytext=(payload_start, line_annotation_height), arrowprops=dict(arrowstyle="<->"), clip_on=True)
    
    plt.axvline(x=payload_start, linestyle='--', color='black')
    
    # Annotation for the cyclic prefix of the preamble
    if ofdm_frame.CP > 0:
        cp_preamble_start = 0
        cp_preamble_end = ofdm_frame.CP * ofdm_frame.M
        plt.text(cp_preamble_start + (cp_preamble_end - cp_preamble_start) // 2, 0.93 * text_annotation_height, "CP", horizontalalignment='center', clip_on=True, color=colors["CP"])
        plt.annotate("", xy=(cp_preamble_end, line2_annotation_height), xytext=(cp_preamble_start, line2_annotation_height), arrowprops=dict(arrowstyle="<->", color=colors["CP"]), clip_on=True)
        plt.vlines(x=cp_preamble_end, ymax=line_annotation_height, linestyles=':', color=colors["CP"], ymin=0)
      
    if symbol_annoation:  
        for i in range(ofdm_frame.N):
            symbol_start = payload_start + i * (ofdm_frame.CP + ofdm_frame.K) * ofdm_frame.M
            symbol_end = payload_start + (i + 1) * (ofdm_frame.CP + ofdm_frame.K) * ofdm_frame.M
            plt.text(symbol_start + (symbol_end - symbol_start) // 2, 0.93 * text_annotation_height, f"Symbol {i}", horizontalalignment='center', clip_on=True, color=colors["info"])
            plt.vlines(x=symbol_end, ymax=line_annotation_height, linestyle='--', color=colors["info"], ymin=0)
        
    if ofdm_frame.CP > 0:
        pass
        
    plt.xlabel("Samples [n]")
    plt.ylabel("Amplitude |x[n]| (normalized)")
    plt.ylim(0, 1.2)
    plt.xlim(0, len(normalized_frame))
    plt.grid(linestyle='--')  
    plt.tight_layout()

def plot_constellation(ofdm_frame: ofdmFrame, view_title: bool = False) -> None:
    """
    Plot the constellation diagram.
    """
    title = "Constellation Diagram"   
    subtitle_params_values = {
        "Payload modulation": ofdm_frame.payload_mod
    }
    subtitle = f"Parameters: {' - '.join(sorted([f'{k}: {v}' for k, v in subtitle_params_values.items()]))}"
    
    plt.figure(title, figsize=square)
    if view_title:
        plt.suptitle(title, fontsize=14, fontweight="bold")
        plt.title(subtitle, fontsize=10, fontstyle="italic")
    plt.scatter(np.real(ofdm_frame.fsymbols_payload_rx), np.imag(ofdm_frame.fsymbols_payload_rx), label="Recieved", c=colors["received"], marker="o")
    plt.scatter(np.real(ofdm_frame.fsymbols_payload), np.imag(ofdm_frame.fsymbols_payload), label="Sent", c=colors["send"], marker="x")
    plt.ylabel("Imaginary")
    plt.xlim(-2, 2)
    plt.ylim(-2, 2)
    plt.xticks(np.arange(-2, 2.1, 0.5))
    plt.yticks(np.arange(-2, 2.1, 0.5))
    plt.grid(True, which='both', linestyle='--')
    plt.legend(loc='lower right')
    plt.tight_layout()

def plot_ber_vs_snr(ber_results: pd.DataFrame, view_title: bool = True, params: dict = None, theoretical: bool = True) -> None:
    """
    Plot the BER vs SNR curve for each payload modulation scheme.
    The ber_results dataframe should contain the following columns:
    - SNR: The SNR value in dB
    - Modulation: The modulation scheme used (BPSK, QPSK)
    - BER: The bit error rate for the corresponding SNR and modulation scheme
    """    
    # Standard theoretical BER functions (these are correct for AWGN channels)
    bpsk_th = lambda x: 0.5 * erfc(np.sqrt(10 ** (x / 10)))
    qpsk_th = lambda x: 0.5 * erfc(np.sqrt(0.5 * 10 ** (x / 10)))
    
    title = "BER vs SNR"
    plt.figure(title, figsize=classical)
    if view_title:
        plt.suptitle(title, fontsize=14, fontweight="bold")
        if params is not None:
            subtitle = f"Parameters: {' - '.join(sorted([f'{k}: {v}' for k, v in params.items()]))}"
            plt.title(subtitle, fontsize=10, fontstyle="italic")
    
    # Theoretical BER functions mapping
    theoretical_ber = {
        "BPSK": bpsk_th,
        "QPSK": qpsk_th
    }
    
    agg_results = ber_results.groupby(["Modulation", "SNR"])["BER"].agg(['mean', 'std']).reset_index()
    modulations = agg_results["Modulation"].unique()
    palette = [colors["line1"], colors["line2"], colors["line3"], colors["line4"], colors["line5"], colors["line6"]]
    markers = ['o', 's', 'x', 'd', '^', 'v']
    color_map = dict(zip(modulations, palette))
    marker_map = dict(zip(modulations, markers[:len(modulations)]))
    
    # Determine SNR range for theoretical curves
    min_snr = agg_results["SNR"].min()
    max_snr = agg_results["SNR"].max()
    snr_range_th = np.linspace(min_snr, max_snr, 100)
    
    # Plot each modulation
    for mod in modulations:
        mod_data = agg_results[agg_results["Modulation"] == mod].sort_values("SNR")
        color = color_map[mod]
        marker = marker_map[mod]
        
        # Plot Simulated Data with error bars
        std_dev = mod_data["std"].fillna(0)
        plt.errorbar(
            mod_data["SNR"],
            mod_data["mean"],
            yerr=std_dev,
            label=f"{mod} (Simulated)",
            color=color,
            marker=marker,
            linestyle='--',
            capsize=3
        )
        
        # Plot Theoretical Data if available
        if theoretical and mod in theoretical_ber:
            ber_th = theoretical_ber[mod](snr_range_th)
            valid_indices = ber_th > 1e-10
            plt.plot(
                snr_range_th[valid_indices],
                ber_th[valid_indices],
                label=f"{mod} (Theoretical)",
                color=color,
                linestyle='-',
                markersize=0
            )
    
    plt.yscale("log")
    plt.xlabel("SNR [dB]")
    plt.ylabel("Bit Error Rate (BER)")
    plt.ylim(bottom=10**(-6))
    plt.legend(loc='lower right')
    plt.grid(True, which='both', linestyle='--')
    plt.tight_layout()