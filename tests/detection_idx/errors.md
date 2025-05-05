### Type of error analysis

During the experiments, some errors seemed to be present in the detection process. 
They have been classified in the following categories:

- **FPGA index error**: This error occurs when the last OFDM frame sample, 
representing the index of the maximum value of the detection metric in the FPGA,
has a value that exceeds the number of samples in the OFDM frame. 

- **Tranmitter error**: This error occurs when the received signal does not match 
the structure of an expected transmitted signal. 
It may occur when the transmitter's signal buffer is not properly filled, or filled
too fast by the UHD application.

- **Frame too short**: This error occurs when the length of the received signal
is smaller than the length of a complete, transmitted OFDM frame.
When the UHD application starts receiving the signal, it way be in a state where the 
FPGA has already detected the beginning of an OFDM frame, but the samples received by
the UHD application start after the first symbol of the considered OFDM frame.

