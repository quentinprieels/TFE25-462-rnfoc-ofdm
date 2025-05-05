# RoadMap

## TODO

### OFDM Library and python simulation

- [x] Clean the different repositories by adding OFDM simulation to `rfnoc-ofdm`
  - [x] Add OFDM lib for simulation
  - [x] Test the OFDM lib on the USRP
  - [x] Add Schmidl & Cox algorithm for synchronization simulation and graphs

### Scripts

- [x] Implement helpful scripts for python packet processing and interaction with UHD

### Documentation

- [ ] Finish the [installation.md](INSTALLATION.md) file
- [ ] Finish the [building.md](BUILDING.md) file
- [ ] Add explanation for building this module, using UHD scripts, creating a new block (where to find possible blocs, how to create the yaml desciption of the block and of the image), how to add IP's, ... => devlopping.md file
- [ ] Add a description of the different blocks and their purpose, how to interact with them, how to use them, etc

### Block validation

- [x] Solve error in the BER after reception => why is there some points not in the constellation?
  This was solved by adding the oversampling factor to the signal like in the default code
- [x] Create a benchmark for the OFDM receiver
  - [x] BER with and without synchronization
  - [x] Metric difference between simulation and hardware
- [x] Find and solve the error in the bus analyzer, why is it not as good as at the beginning?

### FPGA Implementation or ideas

- [x] Add support for the oversampling factor
- [ ] Adding the FFT to the OFDM receiver in hardware (modify the FSM and the python scripts to remove the OFDM prefix)
- [ ] Perform the end of the OFDM demodulation in C++ to target real-time system and having a single to use script
- [ ] Removing the latency of the k/2 delayed signal by starting the *start of frame after max* 77 cycles later
