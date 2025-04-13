# RFNoC OFDM Out-of-Tree Module

This RFNoC out-of-tree module provides an OFDM block for use in RFNoC flowgraphs.
Its main purpose is to provide a partial implementation of an OFDM receiver.

## RFNoC

RFNoC is a heterogeneous processing framework that can be used to implement high
throughput DSP in the FPGA, for Software Defined Radio (SDR) systems, in an
easy-to-use and flexible way. RFNoC and GNU Radio can be used to implement 
heterogenous DSP systems that can span CPU-based hosts, embedded systems and FPGAs.

RFNoC can be used to implement DSP “flow-graphs” where DSP algorithms and IP blocks
are represented as nodes in the graph and the data-flow between them as edges.
RFNoC, which is a network-on-chip architecture, abstracts away the setup associated
with the nodes and edges of the graph and provides seamless and consistent
interfaces to implement IP in the FPGA and software.

See the RFNoC specification for more details on the architecture and how to use it:
https://files.ettus.com/app_notes/RFNoC_Specification.pdf

## Directory Structure (in alphabetical order)

This folder was generated using the `rfnoc_modtool` tool provided by UHD 4.8.0.
EttusResearch recommends sticking to this directory structure and file layout.

* `apps`: This directory is for applications that should get installed into
  the $PATH.

* `cmake`: This directory only needs to be modified if this OOT module will
  come with its own custom CMake modules.

* `examples`: Any example that shows how to use this OOT module goes here.
  Examples that are listed in CMake get installed into `share/rfnoc-ofdm/examples`
  within the installation prefix.

* `fpga/ofdm`: This directory contains the gateware for the HDL modules
  of the individual RFNoC blocks, along with their testbenches, and additional
  modules required to build the blocks. There is one subdirectory for every
  block (or module, or transport adapter). This is also where to define IP that
  is required to build the modules (e.g., Vivado-generated IP).
  Note that this is an "include directory" for gateware, which is why the
  module name ('ofdm') is included in the path. When installing this OOT
  module, these files get copied to the installation path's RFNoC package dir
  (e.g., `/usr/share/uhd/rfnoc/fpga/ofdm`) so the image builder can find
  all the source files when compiling bitfiles that use multiple OOT modules.

* `icores`: Stores full image core files. YAML files in this directory get
  picked up by CMake and get turned into build targets. For example, here we
  include an image core file called `x310_rfnoc_image_core.yml` which defines
  an X310 image core with the ofdm block included. You can build this image
  directly using the image builder, but you can also run `make x310_rfnoc_image_core`
  to build it using `make`.
  These files do not get installed.

* `include/rfnoc/ofdm`: Here, all the header files for the block controllers
  are stored, along with any other include files that should be installed when
  installing this OOT module.
  As with the gateware, the path name mirrors the path after the installation,
  e.g., these header files could get installed to `/usr/include/rfnoc/ofdm`.
  By mirroring the path name, we can write
  `#include <rfnoc/ofdm/ofdm_block_control.hpp>` in our C++ source code, and
  the compilation will work for building this OOT module directly, or in 3rd
  party applications.

* `lib`: Here, all the non-header source files for the block controllers are stored,
  along with any other include file that should not be installed when installing
  this OOT module. This includes the block controller cpp files. All of these
  source files comprise the DLL that gets built from this OOT module.

* `python`: Use this directory to add Python bindings for blocks. Note that if
  the UHD Python API is not found (or Python dependencies for building bindings,
  such as pybind11, are not found) no Python bindings will be generated.

* `rfnoc`: This directory contains all the block definitions (YAML files).
  These block definitions can be read by the RFNoC tools, and will get
  installed into the system for use by other out-of-tree modules.
  Within this directory, there needs to be one subdirectory for every type of
  RFNoC component that this out-of-tree module contains: `blocks` for regular
  RFNoC blocks, `modules` for generic Verilog modules, and `transport_adapters`
  for RFNoC transport adapters.
  Like with the gateware, these get installed into the RFNoC package data
  directory, e.g., `/usr/share/uhd/rfnoc/blocks/*.yml`.

* `tests`: This directory contains files used by the block testbenches or 
  useful files for simulations. This directory is not part of the default
  structure of a RFNoC OOT module.

## Building this module

Before building this module, make sure you have installed the required
software (UHD 4.8.0 on commit `0dede88`, Vivado 2022.1, and the RFNoC
development environment). You can find the instructions for installing
those in the [installation.md](INSTALLATION.md) file of this repository.

To build and install this module, follow these steps:

1. Create a build directory and navigate to it:

    ```bash
    mkdir build
    cd build
    ```

2. Run CMake to configure the build:

    ```bash
    cmake -DUHD_FPGA_DIR=<repo>/fpga/ ../
    make
    ```
    Replace `<repo>` with the path to the [UHD repository](https://github.com/EttusResearch/uhd).

The `make help` command will show you all available build targets for installing, testing and generating the image core bitfiles.

If you want more detailed instructions on how to build this module and use it,
you can check the [building.md](BUILDING.md) file of this repository.