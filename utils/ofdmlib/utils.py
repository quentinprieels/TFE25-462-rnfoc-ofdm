from numpy import array, zeros, reshape
from numpy import sqrt, exp, sign, angle, imag, real
from numpy import complex64, pi


##############
# Exceptions #
##############

class InputError(Exception):
    pass


##################
# Symbol mapping #
##################

def symbol_mapping(bits, const="BPSK"):
    """
    Performs symbol mapping on bit stream <bits>, using the constellation defined by <const>.

    Parameters
    ----------
    bits : List or numpy integer 1D array
        Input bit stream, containing only zeros and ones.
    const : String
        Constellation :
            - "BPSK"  : BPSK constellation;
            - "QPSK"  : QPSK constellation;
            - "16QAM" : 16-QAM constellation;
            - "16PSK" : 16-PSK constellation.

    Raises
    ------
    InputError
        Raised when an incorrect constellation is specified.

    Returns
    -------
    Numpy complex64 1D array
        Output symbol stream.
    """

    if ((array(bits) != 0)*(array(bits) != 1)).any():
        raise InputError("Input bit stream contains incorrect elements !")
    
    if const == "BPSK":
        out = zeros((len(bits),),dtype=complex64)
        out = -2*array(bits) + 1
    elif const == "QPSK":
        out = zeros((int(len(bits)/2),),dtype=complex64)
        bits_I = array(bits[0::2])
        bits_Q = array(bits[1::2])
        out = (-2*bits_I + 1) /sqrt(2) + 1j * (-2*bits_Q + 1) /sqrt(2)
    elif const == "16QAM":
        MSB0 = array(bits[::4])
        MSB1 = array(bits[1::4])
        LSB0 = array(bits[2::4])
        LSB1 = array(bits[3::4])        
        out = (2*LSB0-1) * (3 - 2*LSB1) / sqrt(10) + 1j * (2*MSB0-1) * (3 - 2*MSB1) / sqrt(10)
    elif const == "16PSK":
        MSB0 = array(bits[::4])
        MSB1 = array(bits[1::4])
        LSB0 = array(bits[2::4])
        LSB1 = array(bits[3::4])    
        out = exp(1j * ((2*MSB0-1)*pi/2 + (2*MSB0-1)*(2*MSB1-1)*pi/4 - (2*MSB0-1)*(2*MSB1-1)*(2*LSB0-1)*pi/8 + (2*MSB0-1)*(2*MSB1-1)*(2*LSB0-1)*(2*LSB1-1)*pi/16 + pi/16))
    else:
        raise InputError("Unknown constellation specified : " + const)
    return out.astype(complex64)

def inverse_mapping(symb, const="BPSK"):
    """
    Performs decision on the symbol stream <symb>, using the constellation defined by <const>.
    Decision is performed by selecting the symbol minimising the Euclidian distance with
    the symbols of the constellation (maximum likelihood).

    Parameters
    ----------
    symb : Numpy complex64 1D array
        Input symbol stream.
    const : String
        Constellation :
            - "BPSK"  : BPSK constellation;
            - "QPSK"  : QPSK constellation;
            - "16QAM" : 16-QAM constellation;
            - "16PSK" : 16-PSK constellation.

    Raises
    ------
    InputError
        Raised when an incorrect constellation is specified.

    Returns
    -------
    Numpy integer 1D array
        Output bit stream.
    """
    
    if const == "BPSK":
        out = zeros((len(symb),),dtype=int)
        out = real(symb) < 0
    elif const == "QPSK":
        out = zeros((len(symb)*2,),dtype=int)
        bits_r = -sign(real(symb))
        bits_i = -sign(imag(symb))
        out[0::2] = (bits_r + 1)/2
        out[1::2] = (bits_i + 1)/2
    elif const == "16QAM":
        MSB0 = sign(imag(symb)) > 0
        MSB1 = abs(imag(symb)) < 2/sqrt(10)
        LSB0 = sign(real(symb)) > 0
        LSB1 = abs(real(symb)) < 2/sqrt(10)
        arr = array([MSB0,MSB1,LSB0,LSB1])
        out = reshape(arr.T,(arr.size,))
    elif const == "16PSK":
        phi = angle(symb*exp(-1j*pi/16))
        MSB0 = sign(phi) > 0
        phi -=  (2*MSB0-1)*pi/2
        MSB1 =  ((2*MSB0-1) * sign(phi) + 1)/2
        phi -=  (2*MSB0-1)*(2*MSB1-1)*pi/4
        LSB0 = (-(2*MSB0-1)*(2*MSB1-1) * sign(phi) + 1)/2
        phi +=  (2*MSB0-1)*(2*MSB1-1)*(2*LSB0-1)*pi/8
        LSB1 =  ((2*MSB0-1)*(2*MSB1-1)*(2*LSB0-1) * sign(phi) + 1)/2
        arr = array([MSB0,MSB1,LSB0,LSB1])
        out = reshape(arr.T,(arr.size,))
    else:
        raise InputError("Unknown constellation specified : " + const)
    return out.astype(int)

# Variables
bits = [0,1]
BPSK_const = symbol_mapping(bits,"BPSK")
bits = [0,0,0,1,1,0,1,1]
QPSK_const = symbol_mapping(bits,"QPSK")
bits = [0,0,0,0,0,0,0,1,0,0,1,0,0,0,1,1,0,1,0,0,0,1,0,1,0,1,1,0,0,1,1,1, \
        1,0,0,0,1,0,0,1,1,0,1,0,1,0,1,1,1,1,0,0,1,1,0,1,1,1,1,0,1,1,1,1]
QAM16_const = symbol_mapping(bits,"16QAM")
PSK16_const = symbol_mapping(bits,"16PSK")
