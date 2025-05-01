import numpy as np

def find_max_idx(metric: np.ndarray, threshold: float) -> int:
    """
    Find the index of the maximum value in the metric that is above the threshold.
    """
    state = "SEARCHING" # DETECTING
    max_idx = -1
    max_value = -1
    
    for i in range(len(metric)):
        if state == "SEARCHING":
            if metric[i] > threshold:
                state = "DETECTING"
                max_idx = i
                max_value = metric[i]
        elif state == "DETECTING":
            if metric[i] < threshold:
                return max_idx
            if metric[i] > max_value:
                max_value = metric[i]
                max_idx = i
    return max_idx
