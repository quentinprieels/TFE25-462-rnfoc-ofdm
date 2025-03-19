import sys
import numpy as np
import matplotlib.pyplot as plt

def read_iq_file(filename: str) -> np.ndarray:
    data = np.loadtxt(filename, dtype=np.float32)
    
    if len(data) % 2 != 0:
        raise ValueError(f"Invalid data length: {len(data)} in file {filename}")
    
    sig = data[::2] + 1j * data[1::2]
    sig = np.squeeze(sig)
    
    return sig

def metric_calculator(data, fft_size=16):
    """
    Implements the metric_calculator function as specified in the Verilog code.
    
    Parameters:
    data (np.ndarray): Complex input samples
    fft_size (int): FFT size parameter, must be an even number
    
    Returns:
    np.ndarray: The calculated metric (squared magnitude of the moving average)
    """
    if not isinstance(data, np.ndarray) or not np.iscomplexobj(data):
        raise ValueError("Input must be a numpy array of complex values")
    
    half_fft_size = fft_size // 2
    
    # Step 1: Split the input stream (conceptually, we're creating two identical streams)
    stream_0 = data
    stream_1 = data.copy()
    
    # Step 2: Delay the second stream by HALF_FFT_SIZE
    # This means we're comparing each sample with the one half_fft_size samples ago
    stream_1_delayed = np.roll(stream_1, half_fft_size)
    stream_1_delayed[:half_fft_size] = 0
    
    # Step 3: Take the complex conjugate of the delayed stream
    stream_1_conjugate = np.conj(stream_1_delayed)
    
    # Step 4: Multiply the first stream by the conjugate of the delayed stream
    product = stream_0 * stream_1_conjugate
    
    # Step 5: Moving average (moving sum divided by half_fft_size)
    # Initialize the output array
    moving_avg = np.zeros_like(product)
    
    # Implement moving sum with half_fft_size window
    for i in range(len(product)):
        # Sum last half_fft_size values (with circular buffer behavior)
        window = product[max(0, i - half_fft_size + 1):i + 1]
        if i < half_fft_size - 1:
            # Handle the circular buffer for initial values
            window = np.concatenate((product[-(half_fft_size - 1 - i):], window))
        moving_avg[i] = np.sum(window)
    
    # Step 6: Calculate the squared magnitude of the moving average
    magnitude_squared = np.abs(moving_avg) ** 2
    
    return magnitude_squared
    

def plot_data(data_in: np.ndarray, data_out: np.ndarray, check_data: np.ndarray = None, filename: str = None):
    plt.figure(figsize=(15, 5))
    plt.suptitle("Input and Output Signals comparison", fontsize=14, fontweight='bold')
    plt.title(filename, fontsize=11, fontstyle='italic')
    
    plt.plot(np.abs(data_in), label='Input Signal', color='tab:blue', alpha=0.5)
    plt.plot(np.abs(data_out), label='Output Signal', color='tab:red')
    if check_data is not None:
        plt.plot(np.abs(check_data), label='Check Signal', color='tab:green', alpha=0.8)
    
    plt.xlabel('Sample Index')
    plt.ylabel('Magnitude')
    plt.legend()
    plt.grid()
    plt.show()
    plt.savefig('input_output_comparison.pdf')


def main(args):
    if len(args) != 3:
        print("Usage: python plot_tests.py <input_file> <output_file>")
        return
    
    input_file = args[1]
    output_file = args[2]
    
    input_data = read_iq_file(input_file)
    output_data = read_iq_file(output_file)
    
    filename_title = input_file.split('.')[0]
    plot_data(input_data, output_data, filename=filename_title) #, metric_calculator(input_data, fft_size=16))

if __name__ == '__main__':
    main(sys.argv)
    