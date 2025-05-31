# Building an RFNoC Out-of-Tree Module (OOT)

Before you start, make sure you have installed the necessary software and configured your environment for RFNoC development. You can find the instructions for this in the [installation.md](INSTALLATION.md) document.

If you want to continue working with on the `rfnoc-ofdm` module, or develop your own RFNoC OOT module, check the [development.md](DEVELOPMENT.md) document. It contains some useful tips and tricks about developing RFNoC OOT modules.

## Building and installing the RFNoC OOT module

In order to build this Out-Of-Tree module, first configure the project to be installed in the default location. To achieve this, you can do the following:

```bash
mkdir build
cd build
cmake -DUHD_FPGA_DIR=<repo>/fpga/ ../
```

At this point, run the `make help` command to see the available targets. Some interesting targets are:

- `make rfnoc_block_schmidl_cox_tb`: runs the testbench for the Schmidl & Cox block.
- `make x310_rfnoc_image_core`: builds the X310 RFNoC FPGA image. Make sure to have a valid *Vivado* license,
   otherwise the build will fail.
- `make rfnoc-ofdm`: builds the block controllers for the RFNoC block.
- `make rfnoc_ofdm_python`: builds the Python library for the RFNoC block.
- `rx_to_file`: builds the RX to file example.

You can also run `make` without any arguments to build the default target, which will build the Python library, block controllers, and application.

After building the project, you can install it by running:

```bash
make install
```

**Note 1**: `sudo` may be required to install the project, depending on your system configuration.

**Note 2**: Check the output of the `make install` command to review the different installation paths. It may be needed (as it is the case for Python scripts using the `rfnoc_ofdm` library) to add the `/usr/local/lib/python3.10/site-packages` path to the `PYTHONPATH` environment variable. Inside a python script, you can do this by adding the following lines at the beginning of the script:

```python
import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')
```

## Load a custom FPGA image

In order load a custom FPGA image, you can use the UHD `uhd_image_loader` command. It will flash the FPGA of the USRP with the image binary file specified in argument.

Before starting, make sure you have a `<image>.bin` file, usually located in the `build` directory of your RFNoC OOT module, after you have executed the `make <target>` command. You should also be able to communicate with the USRP device, which is typically done using the `uhd_find_devices` command.

To load the FPGA image, you can navigate to the `build` directory of your RFNoC OOT module, and run the following command:

```bash
uhd_image_loader --args "type=x300,add=<ip_address>" --fpga-path=<image>.bin
```

Replace `<ip_address>` with the IP address of your USRP device and `<image>.bin` with the name of your FPGA image file. You can use the `uhd_find_devices` command to find the IP address of your USRP device if you are unsure.

**Note**: You *must* complete a power cycle of the USRP device after loading a new FPGA image for it to take effect.

## Checking the running FPGA image

In order to get information about the currently running FPGA image of an USRP device, you can use the `uhd_usrp_probe` command. This command is part of the UHD software and is used to probe the USRP device and display its properties.

To check the running FPGA image, you can run the following command:

```bash
uhd_usrp_probe --args "type=x300,addr=<ip_address>"
```

You may ignore the `--args` option if you are using a single USRP device connected to your host machine. Otherwise, replace `<ip_address>` with the IP address of the USRP device you want to probe.

## References

- [EttusResearch Knowledge Base](https://kb.ettus.com/)
- [Getting Started with RFNoC in UHD 4.0](https://kb.ettus.com/Getting_Started_with_RFNoC_in_UHD_4.0)
