# Use the RFNoC OFDM module for OFDM signal processing

This document provides a guide on how to configure the setup and use the application scripts provided in this repository to transmit and receive OFDM signals using the RFNoC OFDM module.

This setup supposes that you have two USRP devices, each of them connected to a host machine. Both devices should be configured, the transmitter with the default FPGA image, and the receiver with the FPGA image you can build from this project. In this work, both USRP devices are connected to a clock source, which is used to synchronize the two devices.

**UCLouvain tips**: The `bluey` machine is used as the transmitter, and the `bingo` machine is used as the receiver.

## Prepare for communication

1. Set up the communication between the host machines and the USRP devices. This can be done by running the following script on both host machines:

    ```bash
    ifconfig enp1s0f0np0 up
    ip addr add 192.168.40.1/24 dev enp1s0f0np0
    ifconfig enp1s0f0np0 mtu 9000

    ifconfig enp1s0f1np1 up
    ip addr add 192.168.50.1/24 dev enp1s0f1np1
    ifconfig enp1s0f1np1 mtu 9000

    ifconfig enp2s0f0np0 up
    ip addr add 192.168.60.1/24 dev enp2s0f0np0
    ifconfig enp2s0f0np0 mtu 9000

    ifconfig enp2s0f1np1 up
    ip addr add 192.168.70.1/24 dev enp2s0f1np1
    ifconfig enp2s0f1np1 mtu 9000

    ifconfig -a
    uhd_find_devices
    ```

    Use the `sudo ./ethsetup.sh` command to run the above script. It will configure the network interfaces to communicate with the USRP devices. If it runs successfully, you should see the USRP devices listed at the end of the script. If not, you may need to restart the network interfaces. Check your connections or restart the host computers.

2. Create a RAM disk on both host machines. This ensures that the data is written by the UHD application to the RAM instead of the hard disk, which can be slow. If the folder does not exist, create a RAM disk folder first with the following command:

   ```bash
    sudo mkdir -p <path_to_ramdisk>
    ```

    then, mount it with the following command:

    ```bash
    sudo mount -t tmpfs -o size=8192m tmpfs <path_to_ramdisk>
    ```

    **UCLouvain tips**: On the host machines used for in the setup, the RAM disk are located
    in the `/export/home/usrpconfig/Desktop/RAMDisk` folder.

3. Copy the `tx_waveforms_radar` or `rx_to_file` binary files (located in the `build/apps` directory) to the RAM disk on both host machines.

   **UCLouvain tips**: On the `bluey machine`, you can run the following command to copy the file:

   ```bash
    cp "/export/home/usrpconfig/Desktop/C++ Files/build-dir/tx_waveforms_radar" /export/home/usrpconfig/Desktop/RAMDisk/
    ```

    And on the `bingo machine`, you can run the following command to copy the file:

    ```bash
    cp /export/home/usrpconfig/Documents/GitHub/TFE25-462/rfnoc-ofdm/build/apps/rx_to_file /export/home/usrpconfig/Desktop/RAMDisk/
    ```

## Generate the transmitted OFDM signal

To generate a OFDM signal to transmit, you can use the `create_tx.py` script located in the `apps` directory.

1. Define the signal parameters you want. **Caution**: the K (number of sub-carriers), CP (cyclic prefix size) and M (oversampling factor) must match the one defined when compiling the FPGA image (see the [rfnoc_block_schmidl_cox.sv](fpga/ofdm/rfnoc_block_schmidl_cox/rfnoc_block_schmidl_cox.sv#L253) file.)

2. Run the `create_tx.py` script with the parameters you defined in the previous step. The script will generate a file containing the OFDM signal, which can be used to transmit the signal. The program will also print adapted commands to run the `tx_waveforms_radar` and the `rx_to_file` applications, based on the parameters you defined.

3. Copy the generated signal file `<tx_file_name>.txt` to the RAM disk on the *transmitter* machine.

4. Use the printed command to run the `tx_waveforms_radar` application on the *transmitter* machine. This application will transmit the OFDM signal using the USRP device. Make sure to run the command from the RAM disk folder.

## Receive the OFDM signal

1. Use the printed command to run the `rx_to_file` application on the *receiver* machine. This application will receive the OFDM signal using the USRP device and save it to a file. Make sure to run the command from the RAM disk folder.

   **Note**: You can modify the parameters of the `rx_to_file` application to change data path followed by the received signal. Run the `rx_to_file` application with the `--help` option to see all the available options.

2. A file containing the received OFDM signal will be generated in the RAM disk folder. The file name will be `<rx_file_name>.dat`.

## Post-process the received OFDM signal

Use the `plot_signal.py` and `demodulate_rx.py` scripts to post-process the received OFDM signal. You need to adapt the parameters in the scripts to match the ones used to generate the transmitted OFDM signal.
