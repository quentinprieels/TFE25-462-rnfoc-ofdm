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

results = [] # Fromat: [{"signal1": "signal1_name", "signal2": "signal2_name", "rmse": 0.1, ...}, {...}, ...]
plot = True # Caution: this can takes time

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
results.append(compare_signals(input, "Input full precision", input_vcd, "Input VCD", plot=plot))


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
results.append(compare_signals(delayed_by_L, "Delayed by L full precision", delayed_by_L_vcd, "Delayed by L VCD", plot=plot))


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
results.append(compare_signals(delayed_conjugate, "Delayed and conjugate full precision", delayed_conjugate_vcd, "Delayed and conjugate VCD", plot=plot))


# Multiply conjugate by input
conjugate_multiplayed = (input * delayed_conjugate[:len(input)]) / 2  #? Factor 2^1
conjugate_multiplayed_truncated = truncate_complex_to_16_bits(conjugate_multiplayed, 32)
conjugate_multiplayed_clipped = clip_complex_to_16_bits(conjugate_multiplayed)
conjugate_multiplayed_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tdata[63:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.mult_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=64,
    is_complex=True
)
results.append(compare_signals(conjugate_multiplayed, "Conjugated multiplayed full precision", conjugate_multiplayed_vcd, "Conjugated multiplayed VCD", plot=plot))
results.append(compare_signals(conjugate_multiplayed, "Conjugated multiplayed full precision", conjugate_multiplayed_truncated, "Conjugated multiplayed truncated", plot=plot))
results.append(compare_signals(conjugate_multiplayed, "Conjugated multiplayed full precision", conjugate_multiplayed_clipped, "Conjugated multiplayed clipped", plot=plot))


# Moving sum to compute the autocorrelation
p_real = moving_sum(np.real(conjugate_multiplayed), L)
truncated_p_real = moving_sum(np.real(conjugate_multiplayed_truncated), L)
clipped_p_real = moving_sum(np.real(conjugate_multiplayed_clipped), L)
p_real_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_i_unscaled_tdata[41:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=42,
    is_complex=False
)
results.append(compare_signals(p_real, "P real full precision", p_real_vcd, "P real VCD", plot=plot))

p_imag = moving_sum(np.imag(conjugate_multiplayed), L)
truncated_p_imag = moving_sum(np.imag(conjugate_multiplayed_truncated), L)
clipped_p_imag = moving_sum(np.imag(conjugate_multiplayed_clipped), L)
p_imag_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_q_unscaled_tdata[41:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_unscaled_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=42,
    is_complex=False
)
results.append(compare_signals(p_imag, "P imaginary full precision", p_imag_vcd, "P imaginary VCD", plot=plot))


# Moving sum truncate
p = p_real + 1j * p_imag
p_truncated = truncate_complex_to_16_bits(p, 42)
p_clipped = clip_complex_to_16_bits(p)
p_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.p_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.autocorrelator.clk",
    bus_size=32,
    is_complex=True
)
results.append(compare_signals(p, "P full precision", p_truncated, "P truncated", plot=plot))
results.append(compare_signals(p, "P full precision", p_clipped, "P clipped", plot=plot))
results.append(compare_signals(p, "P full precision", p_truncated_vcd, "P truncated VCD", plot=plot))
results.append(compare_signals(p_truncated, "P truncated", p_truncated_vcd, "P truncated VCD", plot=plot))

truncated_p = truncated_p_real + 1j * truncated_p_imag
clipped_p = clipped_p_real + 1j * clipped_p_imag
results.append(compare_signals(p, "P full precision", truncated_p, "Truncated P", plot=plot))
results.append(compare_signals(p, "P full precision", clipped_p, "Clipped P", plot=plot))

truncated_p_truncated = truncate_complex_to_16_bits(truncated_p, 26)
truncated_p_clipped = clip_complex_to_16_bits(truncated_p)
results.append(compare_signals(p, "P full precision", truncated_p_truncated, "Truncated P truncated", plot=plot))
results.append(compare_signals(p, "P full precision", truncated_p_clipped, "Truncated P clipped", plot=plot))

clipped_p_truncated = truncate_complex_to_16_bits(clipped_p, 26)
clipped_p_clipped = clip_complex_to_16_bits(clipped_p)
results.append(compare_signals(p, "P full precision", clipped_p_truncated, "Clipped P truncated", plot=plot))
results.append(compare_signals(p, "P full precision", clipped_p_clipped, "Clipped P clipped", plot=plot))



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
results.append(compare_signals(input_magnitude, "Input magnitude full precision", input_magnitude_vcd, "Input magnitude VCD", plot=plot))


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
results.append(compare_signals(r, "R full precision", r_vcd, "R VCD", plot=plot))


# Moving sum truncate
r_truncated = truncate_real_to_16_bits(r, 42)
r_clipped = clip_real_to_16_bits(r)
r_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tdata[15:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.o_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.energy.clk",
    bus_size=16,
    is_complex=False
)
results.append(compare_signals(r, "R full precision", r_truncated, "R truncated", plot=plot))
results.append(compare_signals(r, "R full precision", r_clipped, "R clipped", plot=plot))
results.append(compare_signals(r, "R full precision", r_truncated_vcd, "R truncated VCD", plot=plot))
results.append(compare_signals(r_truncated, "R truncated", r_truncated_vcd, "R truncated VCD", plot=plot))



#####################
# Metric calculator #
#####################
# Metric P squared
p_sqared = np.abs(p) ** 2
p_truncated_squared = np.abs(p_truncated) ** 2
p_truncated_squared_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_p_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
p_truncated_squared_vcd = p_truncated_squared_vcd[1:] # Experimental remark: vcd is 1 sample ahead
results.append(compare_signals(p_sqared, "P squared full precision", p_truncated_squared, "P squared truncated", plot=plot))
results.append(compare_signals(p_sqared, "P squared full precision", p_truncated_squared_vcd, "P squared truncated VCD", plot=plot))
results.append(compare_signals(p_truncated_squared, "P truncated squared", p_truncated_squared_vcd, "P truncated squared VCD", plot=plot))


# Metric Y R squared
r_squared = np.abs(r) ** 2 / 32 #? Factor 2^5
r_truncated_squared = (r_truncated * r_truncated) / 32 #? Factor 2^5
r_truncated_squared_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.abs2_r_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
r_truncated_squared_vcd = r_truncated_squared_vcd[1:] # Experimental remark: vcd is 1 sample ahead
results.append(compare_signals(r_squared, "R squared full precision", r_truncated_squared, "R squared truncated", plot=plot))
results.append(compare_signals(r_squared, "R squared full precision", r_truncated_squared_vcd, "R squared truncated VCD", plot=plot))
results.append(compare_signals(r_truncated_squared, "R truncated squared", r_truncated_squared_vcd, "R truncated squared VCD", plot=plot))


# Metric M
m = p_sqared / r_squared
m_truncated = np.floor((p_truncated_squared * 2 ** 12) / r_truncated_squared)
m_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tdata[31:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.metric_quotient_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=32,
    is_complex=False
)
results.append(compare_signals(m, "M full precision", m_truncated, "M truncated", plot=plot))
results.append(compare_signals(m, "M full precision", m_truncated_vcd, "M truncated VCD", plot=plot))
results.append(compare_signals(m_truncated, "M truncated", m_truncated_vcd, "M truncated VCD", plot=plot))


# Metric N
n = moving_sum(m, CP)
n_truncated = moving_sum(m_truncated, CP)
n_truncated_vcd = load_axi_signal_from_vcd(
    vcd_file, 
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tdata[39:0]",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tvalid",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.m_tready",
    "rfnoc_block_schmidl_cox_tb.dut.mc0.clk",
    bus_size=40,
    is_complex=False
)
results.append(compare_signals(n, "N full precision", n_truncated, "N truncated", plot=plot))
results.append(compare_signals(n, "N full precision", n_truncated_vcd, "N truncated VCD", plot=plot))
results.append(compare_signals(n_truncated, "N truncated", n_truncated_vcd, "N truncated VCD", plot=plot))



###########
# Results #
###########
df = pd.DataFrame.from_records(results)
df.to_csv("results/results.csv", index=False)
print(df)
