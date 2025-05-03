import numpy as np
from vcdvcd import VCDVCD

vcd_file_cached = None
vcd_cached = None

def load_axi_signal_from_vcd(vcdfile: str, 
                             signal_tdata_name: str, signal_tvalid_name: str, signal_tready_name: str, signal_clk_name: str,
                             bus_size: int = 32,
                             is_complex: bool = False) -> np.ndarray:
    """
    Extracts the axi signal from the VCD file and returns it as a numpy array.
    """
    print(f"-> Loading VCD signal {signal_tdata_name}...", end=' ', flush=True)
    
    # Speedup the loading process by caching the VCD file   
    global vcd_file_cached, vcd_cached 
    if vcd_file_cached == vcdfile:
        vcd = vcd_cached
    else:
        vcd_file_cached = vcdfile
        vcd_cached = VCDVCD(vcdfile)
        vcd = vcd_cached
    
    # Get the signal data
    signal_tdata = vcd[signal_tdata_name]
    signal_tvalid = vcd[signal_tvalid_name]
    signal_tready = vcd[signal_tready_name]
    signal_clk = vcd[signal_clk_name]
    signal_values = []
    
    # Get the clock edges (rising edges)
    clk_rising_edges = [t for t, v in signal_clk.tv if int(v) == 1]
    
    # Iterate over the signal data
    for timestamp in clk_rising_edges:
        # Check if the signal is valid and ready
        if signal_tvalid[timestamp] == 'x'or int(signal_tvalid[timestamp]) == 0 or int(signal_tready[timestamp] == 0):
            continue
        
        # Sample the signal at the clock edge
        tdata_value = signal_tdata[timestamp]
        
        # Get the tdata value
        tdata_value = signal_tdata[timestamp]
        
        # Add 0 before the value to ensure it's 32 bits long
        if len(tdata_value) < bus_size:
            tdata_value = '0' * (bus_size - len(tdata_value)) + tdata_value
    
        if is_complex:
            real_part = int(tdata_value[:bus_size//2], 2) # MSB
            imag_part = int(tdata_value[bus_size//2:], 2) # LSB
            
            # Get the sign bits
            real_sign = real_part >> (bus_size//2 - 1) & 1
            imag_sign = imag_part >> (bus_size//2 - 1) & 1
            
            # Get the data part
            real_part = real_part & ((1 << (bus_size//2 - 1)) - 1)
            imag_part = imag_part & ((1 << (bus_size//2 - 1)) - 1)
            
            # Convert to signed integers
            real_part = np.where(real_sign, real_part - (1 << (bus_size//2 - 1)), real_part)
            imag_part = np.where(imag_sign, imag_part - (1 << (bus_size//2 - 1)), imag_part)
            
            # Convert to complex signal
            complex_value = real_part + 1j * imag_part
            signal_values.append(complex_value)
        
        else:
            data = int(tdata_value, 2)
            
            # Get the sign bit
            sign_bit = data >> (bus_size - 1) & 1
            
            # Get the data part
            data = data & ((1 << (bus_size - 1)) - 1)
            
            # Convert to signed integer
            data = np.where(sign_bit, data - (1 << (bus_size - 1)), data)
            signal_values.append(data)
    print(f"Loaded.")
    return np.array(signal_values)
