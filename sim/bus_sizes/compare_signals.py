import pandas as pd
import numpy as np

from complex_signal import read_sc16_file, moving_sum, truncate_complex_to_16_bits, truncate_real_to_16_bits, clip_complex_to_16_bits, clip_real_to_16_bits
from metrics import compare_signals
from vcd_helpers import load_axi_signal_from_vcd

# Simulation parameters
signal_file = "data/rx_samples_raw.sc16.dat"
vcd_file = "data/rfnoc_block_schmidl_cox_tb.vcd"
K = 1024
L = K // 2
CP = 128

simulation_vs_vcd_results = {} # Fromat: {signal: {metric1: value1, metric2: value2, ...}, ...}

###########################
# Symbol auto-correlation #
###########################
# Input signals
input = read_sc16_file("data/rx_samples_raw.sc16.dat")
input_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.i_lat_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.i_lat_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.i_lat_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=32,
    is_complex=True
    )
input_vcd = input_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(input), len(input_vcd))
simulation_vs_vcd_results["Input signal"] = compare_signals(input[:min_len], input_vcd[:min_len])


# Delay by L samples
delayed_by_L = np.concatenate((np.zeros(L, dtype=input.dtype), input))
delayed_by_L_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_cpy1_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_cpy1_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_cpy1_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=32,
    is_complex=True
)
delayed_by_L_vcd = delayed_by_L_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(delayed_by_L), len(delayed_by_L_vcd))
simulation_vs_vcd_results["Delayed by L"] = compare_signals(delayed_by_L[:min_len], delayed_by_L_vcd[:min_len])


# Conjugate the delayed signal
delayed_conjugate = np.conjugate(delayed_by_L)
delayed_conjugate_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_conj_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_conj_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.dely_conj_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=32,
    is_complex=True
)
delayed_conjugate_vcd =  delayed_conjugate_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(delayed_conjugate), len(delayed_conjugate_vcd))
simulation_vs_vcd_results["Delayed and conjugate"] = compare_signals(delayed_conjugate[:min_len], delayed_conjugate_vcd[:min_len])


# Multiply conjugate by input
conjugate_multiplayed = (input * delayed_conjugate[:len(input)]) / 2  #? Factor 2^1
conjugate_multiplayed_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tdata[63:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=64,
    is_complex=True
)
min_len = min(len(conjugate_multiplayed), len(conjugate_multiplayed_vcd))
simulation_vs_vcd_results["Conjugated multiplayed"] = compare_signals(conjugate_multiplayed[:min_len], conjugate_multiplayed_vcd[:min_len])


# Moving sum to compute the autocorrelation
p_real = moving_sum(np.real(conjugate_multiplayed), L)
p_real_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_i_unscaled_tdata[41:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=42,
    is_complex=False
)
min_len = min(len(p_real), len(p_real_vcd))
simulation_vs_vcd_results["P real"] = compare_signals(p_real[:min_len], p_real_vcd[:min_len])

p_imag = moving_sum(np.imag(conjugate_multiplayed), L)
p_imag_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_q_unscaled_tdata[41:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=42,
    is_complex=False
)
min_len = min(len(p_imag), len(p_imag_vcd))
simulation_vs_vcd_results["P imaginary"] = compare_signals(p_imag[:min_len], p_imag_vcd[:min_len])


# Moving sum truncate
p_truncated = truncate_complex_to_16_bits(p_real + 1j * p_imag, 42)
p_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=32,
    is_complex=True
)
min_len = min(len(p_truncated), len(p_truncated_vcd))
simulation_vs_vcd_results["P truncated"] = compare_signals(p_truncated[:min_len], p_truncated_vcd[:min_len])



#################
# Symbol energy #
#################
# Input signal magnitude
input_magnitude = np.abs(input) ** 2
input_magnitude_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.abs_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.abs_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.abs_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.clk",
    bus_size=32,
    is_complex=False
)
input_magnitude_vcd = input_magnitude_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(input_magnitude), len(input_magnitude_vcd))
simulation_vs_vcd_results["Input magnitude"] = compare_signals(input_magnitude[:min_len], input_magnitude_vcd[:min_len])


# Moving sum to compute the energy
r = moving_sum(input_magnitude, L)
r_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.sum_unscaled_tdata[41:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.sum_unscaled_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.sum_unscaled_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.clk",
    bus_size=42,
    is_complex=False
)
min_len = min(len(r), len(r_vcd))
simulation_vs_vcd_results["R"] = compare_signals(r[:min_len], r_vcd[:min_len])


# Moving sum truncate
r_truncated = truncate_real_to_16_bits(r, 42)
r_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tdata[15:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.clk",
    bus_size=16,
    is_complex=False
)
min_len = min(len(r_truncated), len(r_truncated_vcd))
simulation_vs_vcd_results["R truncated"] = compare_signals(r_truncated[:min_len], r_truncated_vcd[:min_len])



#####################
# Metric calculator #
#####################
# Metric P squared
p_squared = np.abs(p_truncated) ** 2
p_squared_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
p_squared_vcd = p_squared_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(p_squared), len(p_squared_vcd))
simulation_vs_vcd_results["P squared"] = compare_signals(p_squared[:min_len], p_squared_vcd[:min_len])


# Metric Y R squared
r_squared = (r_truncated * r_truncated) / 32 #? Why
r_squared_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
r_squared_vcd = r_squared_vcd[1:] # Experimental remark: vcd is 1 sample ahead
min_len = min(len(r_squared), len(r_squared_vcd))
simulation_vs_vcd_results["R squared"] = compare_signals(r_squared[:min_len], r_squared_vcd[:min_len])


# Metric M
metric_m = np.floor((p_squared * 2 ** 12) / r_squared)
metric_m_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
min_len = min(len(metric_m), len(metric_m_vcd))
simulation_vs_vcd_results["M"] = compare_signals(metric_m[:min_len], metric_m_vcd[:min_len])


# Metric N
metric_n = moving_sum(metric_m, CP)
metric_n_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tdata[39:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=40,
    is_complex=False
)
print_idx = 2300
print_len = 10
min_len = min(len(metric_n), len(metric_n_vcd))
simulation_vs_vcd_results["N"] = compare_signals(metric_n[:min_len], metric_n_vcd[:min_len])


###########
# Results #
###########
df = pd.DataFrame.from_dict(simulation_vs_vcd_results, orient='index')
df.to_csv("results/simulation_vs_vcd.csv")
print(df)