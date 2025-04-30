import numpy as np

def add_noise(tsymbol: np.ndarray, SNR: float, random_generator: np.random.Generator = None) -> np.ndarray:
    """
    Add AWG noise to the given frame.
    """
    if random_generator is None:
        random_generator = np.random.default_rng()
    
    if SNR == np.inf:
        return tsymbol
    
    signal_power = np.mean(abs(tsymbol) ** 2)
    noise_power = signal_power * 10 ** (-SNR / 10)
    noise_frame = np.sqrt(noise_power / 2) * (random_generator.normal(size=len(tsymbol)) + 1j * random_generator.normal(size=len(tsymbol)))
    noisy_frame = tsymbol + noise_frame
    return noisy_frame