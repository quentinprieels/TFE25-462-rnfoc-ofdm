# Installation instructions for RFnOC toolchain

This document provides instructions for *installing* the required software and
dependencies needed to develop, build, install, and run the RFNoC OFDM module.
More detailed instructions about the build process can be found in the
[building.md](BUILDING.md) file.

The tool chain is inspired by the one [proposed by Ettus](https://files.ettus.com/manual/md_usrp3_build_instructions.html)
to program their USRP devices.
It is part of the [USRP Hardware Driver and USRP Manual (UHD)](https://files.ettus.com/manual/index.html).
This tool chain uses an [USRP-2944R](https://www.ni.com/fr-be/shop/model/usrp-2944.html) device
(also called [X310 + UBX(x2)](https://www.ettus.com/all-products/usrp-x310/) in the Ettus nominal).
It embeds a Xilinx Kintex-7 FPGA (XC7K410T).

## Table of contents

- [Installation instructions for RFnOC toolchain](#installation-instructions-for-rfnoc-toolchain)
  - [Table of contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Install the UHD library](#install-the-uhd-library)
    - [UHD Binary Installation](#uhd-binary-installation)
    - [Cloning the UHD repository](#cloning-the-uhd-repository)
    - [Verifying the UHD installation](#verifying-the-uhd-installation)
  - [Install Vivado](#install-vivado)
    - [Download and install](#download-and-install)
    - [Troubleshooting](#troubleshooting)
    - [Install the required patches](#install-the-required-patches)
    - [Use external Vivado installation](#use-external-vivado-installation)
    - [Test the Vivado installation](#test-the-vivado-installation)
    - [Connect to a licensed server](#connect-to-a-licensed-server)
  - [ModelSim](#modelsim)
  - [GNU Radio](#gnu-radio)

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

The UHD library is a framework used to communicate between the host computer
and the USRP devices. This software is used to program the FPGA and
configure the data path as well as the data transfer between the host and the USRP
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

See <https://files.ettus.com/manual/page_install.html#install_linux> for more details about UHD
binary installation.

### Cloning the UHD repository

You should also clone the [UHD repository](https://github.com/EttusResearch/uhd),
as it contains some scripts and examples that are useful for the development of RFNoC modules.
To do so, run the following command:

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
If you do not see any devices, make sure you Ethernet connection is working and that the USRP devices
are powered on. You can also check the
[Device & Usage manual](https://files.ettus.com/manual/page_usrp_x3x0.html) and follow the instructions
to set up the USRP devices.

## Install Vivado

Vivado is the tool used to build the FPGA images located on the USRP devices.
The [FPGA Manual](https://files.ettus.com/manual/md_usrp3_build_instructions.html#autotoc_md110)
provided by Ettus recommends using the Vivado 2022.1 version.

### Download and install

> If you can access an external installation of Vivado, you can skip this section. The next sections
> could still be useful to install the patches, or make sure the RFNoC tool chain will found the external installation.

To download Vivado 2022.1, you can use the [Xilinx website](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools.html).
You will need to create an account to download the software.
Make sure to select the correct version (2022.1) and the correct platform (Linux).

Install Vivado by following the instructions provided by Xilinx.

**Note 1**: To save disk space and installation time, you can install only the support for the FPGA's
you intend to use. (i.e. Kintex-7 to work with the USRP mentioned above)

**Note 2**: The recommended installation directory is `/opt/Xilinx/`. Change it when you are asked
for the installation directory.

### Troubleshooting

- **Cannot write to /opt/Xilinx/ Check the read/write permissions**

    If the warning *Cannot write to /opt/Xilinx/ Check the read/write permissions* appears,
    create the directory `/opt/Xilinx/` and give write permissions to the user. To do so, run the following commands:

    ```bash
    sudo mkdir /opt/Xilinx/
    sudo chown $USER:$USER /opt/Xilinx/
    ```

    Then, re-select the directory `/opt/Xilinx/` in the installation process.

- **Cannot compile the RFNoC module**

    If you cannot compile the RFNoC module, make sure you have installed the correct version of Vivado.
    Some tool versions are hard-coded in the building scripts provided in the UHD repository.

### Install the required patches

The AR76780 Patch for Vivado 2022.1 is required to work with the USRP devices.

To install it, download the patch (*AR76780_vivado_2021_1_preliminary_rev1.zip*) from the
[AMD website](https://adaptivesupport.amd.com/s/article/76780?language=en_US).

Then, extract the content of the archive to the directory where Vivado is installed,
under the `patches/AR76780` directory.  If you installed Vivado at the recommended directory,
the patch should be installed in `/opt/Xilinx/Vivado/2021.1/patches/AR76780/vivado/...`.

### Use external Vivado installation

If you want to use an external installation of Vivado (for example, if you can mount the installation
directory from a remote server), it is recommended to create a symbolic link to the installation directory.
This ensures that the RFNoC tool chain will find the installation directory and use it to build the FPGA images.

To do so, run the following command (or an adjusted version of it):

```bash
sudo ln -s /path/to/vivado /opt/Xilinx/
```

If you created the symbolic link successfully, the command `ls /opt/Xilinx/Vivado/2021.1` should
output the content of the Vivado installation directory and look like this:

```bash
bin  common  data  doc  examples  fonts  gnu  hybrid_sim  ids_lite  include  lib  lnx64  patches  platforms  reportstrategies  scripts  settings64.csh  settings64.sh  src  strategies  tps
```

### Test the Vivado installation

To test if the Ettus tool chain can find your Vivado installation, navigate to the `x310` directory of
the UHD repository and run the following command:

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

**Note**: All the scripts in the UHD repository are designed to be run from a bash shell.
If you are using a different shell or encounter some problems by running the provided scripts
change the shell to bash before running the script (using the `bash` command for instance).

### Connect to a licensed server

To be able to build the FPGA images, you will need to have a valid license for Vivado.
If you have access to a license server, you can configure Vivado to load the licenses
from it by setting the `XILINXD_LICENSE_FILE` environment variable.

You can either export the variable in your `.bashrc` file, `export` it in the terminal before running the
`setupenv.sh` script, or add it to your `/etc/environment` file. To do so, run the following command:

```bash
echo "XILINXD_LICENSE_FILE=<port>@<license_server>" | sudo tee -a /etc/environment
```

To verify that the license server is correctly configured, run the `echo $XILINXD_LICENSE_FILE`
command. You can also run the `vivado` command (if you have set up the environment as explained above),
then click on the *Help* menu and select *Manage License*.
In the *View License Status* tab, you should see the status of your license.

## ModelSim

> ModelSim is not required to simulate the RFNoC blocks, as *XSim*, the built-in simulator of Vivado,
> can be used instead.

ModelSim is a simulation software for hardware description languages (HDL) such as VHDL and Verilog, both
used in this project. The [Ettus documentation](https://files.ettus.com/manual/md_usrp3_sim_running_testbenches.html)
explains how to install and use ModelSim if you want to rely on it for simulation.

**Note**: If your ModelSim installation is not recognized by the RFNoC tool chain, it may be due to the regular expression
used by the provided scripts to determine the ModelSim version (see the *Prepare ModelSim environment*
section in the `<uhd>/fpga/usrp3/tools/scripts/setupenv_base.sh` script).

## GNU Radio

> GNU Radio is not required to run this RFNoC module, and was not used during this project.
> However, it can be a useful tool to abstract UHD applications and make them easier to develop, maintain,
> use and deploy.

GNU Radio is a free & open-source software development toolkit that provides signal processing blocks
to implement software radios. It is compatible with UHD, the software driver for USRP devices.

To install GNU Radio, you can follow the instructions provided in the
[GNU Radio installation guide](https://wiki.gnuradio.org/index.php/InstallingGR).

**Note**: Some recent versions of GNU Radio cannot be installed using the `apt` package manager
(at least not on the Ubuntu 22.04 LTS version used in this work, in May 2025). Older versions of
GNU Radio use a lower version of the `libuhd` package, making them incompatible with recent builds
of FPGA images. This is the reason why C++ applications using UHD 4.8 where used in this work.
