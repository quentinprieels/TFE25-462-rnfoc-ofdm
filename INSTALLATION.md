# Installation instructions for RFnOC toolchain

This document provides instructions for *installing* the required software and
dependencies needed to develop, build, install, and run the RFNoC OFDM module.
More detailed instructions about the build process can be found in the
[building.md](BUILDING.md) file.

The toolchain is inspired by the one [proposed by Ettus](https://files.ettus.com/manual/md_usrp3_build_instructions.html) to program their USRP devices. It is part of the [USRP Hardware Driver and USRP Manual (UHD)](https://files.ettus.com/manual/index.html). This toolchain uses an [USRP-2944R](https://www.ni.com/fr-be/shop/model/usrp-2944.html) device (also called [X310 + UBX(x2)](https://www.ettus.com/all-products/usrp-x310/) in the Ettus nominal). It embeds a Xilinx Kintex-7 FPGA (XC7K410T).

## Prerequisites

Before installing the required software, make sure you have the following prerequisites installed:

- 100 GB of free disk space
- 16 GB of RAM
- A supported version of Ubuntu (22.04 LTS or later is recommended)
- Python 3.8 or later
- Add the UHD PPA to your system:
    ```bash
    sudo add-apt-repository ppa:ettusresearch/uhd
    ```
    and update your package list:
    ```bash
    sudo apt update
    ```
- Git, a version control system used to clone the UHD repository:
    ```bash
    sudo apt install git
    ```

## Install the UHD library

The UHD library is the software used to communicate between the host computer
and the USRP devices. This software framework is used to program the FPGA and
configure the datapath as well as the data transfer between the host and the USRP
devices.

### UHD Binary Installation

To install the UHD library, run the following command:
```bash
sudo apt install libuhd-dev uhd-host
```
This command will install the UHD library and its dependencies. After installation,
you can check if the UHD library is installed correctly by running the 
`dpkg -l | grep uhd | awk '{print $2 }'` command. If the UHD library is installed correctly, 
you should the following output:
```txt
libuhd-dev
libuhd4.8.0:amd64
python3-uhd
uhd-host
```
Note that the version of the UHD library may vary. 

See https://files.ettus.com/manual/page_install.html#install_linux for more details about UHD
binary installation.

### Cloning the UHD repository

You should also clone the [UHD repostory](https://github.com/EttusResearch/uhd), 
as it contains some scripts and examples that are useful for the development of RFNoC modules. To do so, run the following command:
```bash
git clone https://github.com/EttusResearch/uhd
```

### Verifying the UHD installation
After installing the UHD library, you can verify the installation by running the following command:
```bash
uhd_find_devices
```
This command will search for USRP devices connected to your computer. 
If the UHD library is installed correctly, you should see a list of available USRP devices.
If you do not see any devices, make sure you ethernet connection is working and that the USRP devices 
are powered on. You can also check the 
[Device & Usage manual](https://files.ettus.com/manual/page_usrp_x3x0.html) and follow the instructions 
to set up the USRP devices. 

## Install Vivado

Vivado is the software used to build the FPGA images located on the USRP devices. 
The [FPGA Manual](https://files.ettus.com/manual/md_usrp3_build_instructions.html#autotoc_md110) 
provided by Ettus recommends using the Vivado 2022.1 version.

### Download and install

> If you can access an external installation of Vivado, you can skip this section. The next sections
> could still be useful to install the patches, or make sure the RFNoC toolchain will found 
> the external installation.

To dowload vivado 2022.1, you can use the [Xilinx website](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools.html). 
You will need to create an account to download the software. 
Make sure to select the correct version (2022.1) and the correct platform (Linux).

Install Vivado by following the instructions provided by Xilinx.
> To save disk space and installation time, you can install only the support for the FPGAs you intend to use. (i.e. Kintex-7 to work with the USRP mentioned above)

> The recommended installation directory is `/opt/Xilinx/`. Change it when you are asked for the installation directory. 

#### Troubleshooting

- **Cannot write to /opt/Xilinx/ Check the read/write permissions**

    If the warning *Cannot write to /opt/Xilinx/ Check the read/write permissions* appears, create the directory `/opt/Xilinx/` and give the write permissions to the user. To do so, run the following commands:
    ```bash
    sudo mkdir /opt/Xilinx/
    sudo chown $USER:$USER /opt/Xilinx/
    ```
    and re-select the directory `/opt/Xilinx/` in the installation process.

### Install the required patches

The AR76780 Patch for Vivado 2022.1 is required to work with the USRP devices. 

To install it, download the patch (*AR76780_vivado_2021_1_preliminary_rev1.zip*) from the 
[AMD website](hhttps://adaptivesupport.amd.com/s/article/76780?language=en_US).

Then, extract the content of the archive to the directory where Vivado is installed, under the `patches/AR76780` directory.  If you installed Vivado at the recommended directory, the patch should be installed 
in `/opt/Xilinx/Vivado/2021.1/patches/AR76780/vivado/...`.

### Use external vivado installation

If you want to use an external installation of Vivado (for example, if you can mount the installation 
directory from a remote server), it is recommended to create a symbolic link to the installation directory.
This esures that the RFNoC toolchain will find the installation directory and use it to build the FPGA images.

To do so, run the following command (or an adjusted version of it):
```bash
sudo ln -s /path/to/vivado /opt/Xilinx/
```
If you created the symbolic link successfully, the command `ls /opt/Xilinx/Vivado/2021.1` should output the content of the Vivado installation directory and look like this:
```bash
bin  common  data  doc  examples  fonts  gnu  hybrid_sim  ids_lite  include  lib  lnx64  patches  platforms  reportstrategies  scripts  settings64.csh  settings64.sh  src  strategies  tps
```

### Test the Vivado installation

To test if the Ettus toolchain can find your vivado installation, navigate to the `x310` directory of the UHD repository and run the following command:
```bash
cd uhd/fpga/usrp3/top/x300
source setupenv.sh
```
You should see the following output:
```txt
Setting up a 64-bit FPGA build environment for the USRP-X3x0...
- Vivado: Found (/opt/Xilinx/Vivado/2021.1/bin)
          Installed version is Vivado v2021.1_AR76780 (64-bit)
```

> All the scripts in the UHD repository are designed to be run from a `bash` shell. If you are using a 
> different shell, change the shell to `bash` before running the script (using the `bash` command for 
> example).

### Connect to a licensed server

To be able to build the FPGA images, you need to have a valid license for Vivado. If you have a license
server, you can connect to it by configuring the `XILINXD_LICENSE_FILE` environment variable. You can
either export the variable in your `.bashrc` file `export` it in the terminal before running the
`setupenv.sh` script, or add it to your `/etc/environment` file. To do so, run the following command:
```bash
echo "XILINXD_LICENSE_FILE=<port>@<license_server>" | sudo tee -a /etc/environment
```

To verify that the license server is correctly configured, run the `echo $XILINXD_LICENSE_FILE`
command. You can also run the `vivado` command, then click on the `Help` menu and select `Manage License`.
In the `View License Status` tab, you should see the status of your license. 

## Install ModelSim

TODO


## GNU Radio

TODO

