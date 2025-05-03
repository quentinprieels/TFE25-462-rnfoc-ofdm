import unittest
import numpy as np

from complex_signal import complexSignal

class TestComplexSignal(unittest.TestCase):
    signal_size = 24    
    real_part = np.array([
        0b0000_0000_0000_0000_0000_0000,
        0b1111_1111_1111_1111_1111_1111,
        0b1111_1111_1111_1111_0000_0000,
        0b1010_1010_1010_1010_1010_1010,
        0b0110_1010_1011_1100_0010_1010,
        0b1000_1011_1100_1101_0101_0110,
        0b0000_0000_0000_1010_0101_0110,
    ])
    
    imag_part = np.array([
        0b0000_0000_0000_0000_0000_0000,
        0b0111_1111_1111_1111_1111_1111,
        0b0000_1111_0000_1111_0000_1111,
        0b1000_1010_1001_0111_0101_0101,
        0b1100_0110_1000_1110_1011_0101,
        0b0011_0101_0110_0011_0101_1110,
        0b1111_1111_1100_0110_0101_1011,
    ])
    
    signal = real_part + 1j * imag_part
    
    
    def setUp(self):
        self.complex_signal = complexSignal()
        self.complex_signal._load_binary(self.real_part, self.imag_part, self.signal_size)
    
    def test_load_binary(self):
        """
        Use the https://www.exploringbinary.com/twos-complement-converter/ website
        to convert the binary numbers to decimal.
        """
        expected_real = np.array([0, -1, -256, -5592406, 6994986, -7615146, 2646])
        expected_imag = np.array([0, 8388607, 986895, -7694507, -3764555, 3498846, -14757])            
        
        np.testing.assert_array_equal(np.real(self.complex_signal.csignal), expected_real)
        np.testing.assert_array_equal(np.imag(self.complex_signal.csignal), expected_imag)
            
    
    def test_truncate_to_16_bits(self):
        self.complex_signal.truncate_to_16_bits(self.signal_size)
        
        # Check if the signal is truncated correctly
        expected_real = np.array([
            0b0000_0000_0000_0000,
            0b1111_1111_1111_1111,
            0b1111_1111_1111_1111,
            0b1010_1010_1010_1010,
            0b0110_1010_1011_1100,
            0b1000_1011_1100_1101,
            0b0000_0000_0000_1010,
        ])
        
        expected_imag = np.array([
            0b0000_0000_0000_0000,
            0b0111_1111_1111_1111,
            0b0000_1111_0000_1111,
            0b1000_1010_1001_0111,
            0b1100_0110_1000_1110,
            0b0011_0101_0110_0011,
            0b1111_1111_1100_0110
        ])
        
        expected_signal = complexSignal()
        expected_signal._load_binary(expected_real, expected_imag, 16)
        
        np.testing.assert_array_equal(self.complex_signal.real_part, expected_signal.real_part)
        np.testing.assert_array_equal(self.complex_signal.imag_part, expected_signal.imag_part)
        
    
    def test_clip_to_16_bits(self):
        self.complex_signal.clip_to_16_bits()
        
        # Check if the signal is clipped correctly
        expected_real = np.array([0, -1, -256, -32768, 32767, -32768, 2646])
        expected_imag = np.array([0, 32767, 32767, -32768, -32768, 32767, -14757])
        
        np.testing.assert_array_equal(self.complex_signal.real_part, expected_real)
        np.testing.assert_array_equal(self.complex_signal.imag_part, expected_imag)

      
if __name__ == '__main__':
    unittest.main()
