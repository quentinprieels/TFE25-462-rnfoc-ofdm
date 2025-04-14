# Building an Out-of-Tree Module (OOT) for RFNoC

Many information and instructions provided in this document where taken from the 
[Knowledge base of Ettus Research](https://kb.ettus.com/), and especially from the
[Getting Started with RFNoC in UHD 4.0](https://kb.ettus.com/Getting_Started_with_RFNoC_in_UHD_4.0) page. 

## Load a custom FPGA image

To load a custom FPGA image, you can use the `uhd_image_loader` command. 
This command is part of the UHD softwareand is used to load FPGA images onto the
USRP device.

Before starting, make sure you have a `<image>.bin` file, usually located in the 
`build` directory of your RFNoC OOT module, after you have executed the 
`make <target>` command. You should also be able to communicate with the USRP
device, which is typically done using the `uhd_find_devices` command.

To load the FPGA image, you can navigate to the `build` directory of your RFNoC
OOT module, and run the following command:

```bash
uhd_image_loader --args "type=x300,add=<ip_address>" --fpga-path=<image>.bin
```
Replace `<ip_address>` with the IP address of your USRP device and `<image>.bin`
with the name of your FPGA image file.

You **must** complete a power cycle of the USRP device after loading a new FPGA image for it to take effect.

## Checking the running FPGA image

To get information about the currently running FPGA image of an USRP device,
you can use the `uhd_usrp_probe` command. This command is part of the UHD software
and is used to probe the USRP device and display its properties.

To check the running FPGA image, you can run the following command:

```bash
uhd_usrp_probe --args "type=x300,addr=<ip_address>"
```
You may ignore the `--args` option if you are using a single USRP device connected
to your host machine.

