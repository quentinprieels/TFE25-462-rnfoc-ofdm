# Developing and Out-Of-Tree Module in RFNoC

- RFNoC specification
- Gain example
- refers to building.md file for running a simulation and flashing the FPGA

## Create a new OOT module

To create a new RFNoC OOT module, you can use the `rfnoc_modtool` command. This command will
create a new directory with the default structure of your module. To do so, run the following:

```bash
rfnoc_modtool createmodule <module_name>
```

This will create a new directory called `rfnoc-<module_name>`. You can explore the directory and read the
auto-generated `README.md` file to understand the role of each subdirectory.

## Create a new RFNoC block

### Create a new RFNoC Block with `rfnoc_modtool`

To create a new RFNoC block, you have first to define its components in the YAML file corresponding to the
block. Create a new file in the `rfnoc/block/` directory called `<block_name>.yml`. This file should contain the
definition of the block, including its parameters, inputs, and outputs.

Check the [schmidl_cox.YAML](rfnoc/blocks/schmidl_cox.YAML) of this repository or the
[gain.YAML](https://github.com/EttusResearch/uhd/blob/master/host/examples/rfnoc-gain/rfnoc/blocks/gain.YAML)
example from EttusResearch.

The [RFNoC specification](https://files.ettus.com/app_notes/RFNoC_Specification.pdf) provides a detailed
description of the YAML file format and the parameters that can be defined.

Once the block definition is complete, use the `rfnoc_modtool` command to generate the Verilog files for the block
and the testbench. Run the following command:

```bash
rfnoc_modtool add <block_name>
```

This will create a new directory called `rfnoc/fpga/<module_name>/<block_name>`.

**Note**: If you modify the YAML file, you need to run the `rfnoc_modtool` command again to regenerate the Verilog files.
This will overwrite the existing `noc_shell_<block_name>.sv`, `rfnoc_block_<block_name>.sv` and `rfnoc_block_<block_name>_tb.sv` files.
Make sure to back up them to avoid losing custom changes made to them.

### Exploring the generated files

- `noc_shell_<block_name>.sv`: contains the NoC shell for the block. It makes the conversion between incoming RFNoC packets
  and internal signals of the block.
- `rfnoc_block_<block_name>.sv`: contains the Verilog code for the block.
- `rfnoc_block_<block_name>_tb.sv`: contains the testbench for the block.
- `Makefile.srcs`: contains the list of the files to be synthesized. If you want to add custom file, or create System Verilog
  modules, you can add them here.
- `Makefile`: Makefile for the block simulation and synthesis.

## Using IP blocks

A lot of IP blocks, either from Xilinx or from the RFNoC repository can be used in your design. Depending on the type,
they are added to your project in different ways:

- **RFNoC repository**: Some Verilog module are available [in the UHD FPGA repository](https://github.com/EttusResearch/uhd/tree/master/fpga/usrp3/lib/rfnoc)
  you can directly instantiate them in your design.
- **Xilinx in-tree IP**: Some [Xilinx IP blocks](https://github.com/EttusResearch/uhd/tree/master/fpga/usrp3/lib/ip) can be used in your design.
  To instantiate them, you will need to specify then in the *Design Specific* section of the `Makefile` file. Refers to the gain example
  to see how to do it. The `<ip_name>.xci` contains the IP block definition and parameters values.
- **Xilinx out-of-tree IP**: You can add your own IP blocks to your design. Refers to the gain example to see how to add them. You will need
  to create additional folder in your project, specify them in the `Makefile` and in your block YAML file.

## Exploring waveforms

Once you have write some logic in your block, you can simulate your design using the `make rfnoc_block<block_name>_tb` command. This will
launch the simulation as specified in the testbench file. You can add the `GUI=1` option to the command to open Vivado GUI and explore the
waveforms.

**Tips**: If you do not like the Vivado GUI, or that the program is too slow due to SSH connection to an external installation, you can dump
the waveforms in a VCD file, by adding the following lines in the testbench file:

```verilog
initial begin : tb_main
    $dumpfile("waveform.vcd");
    $dumpvars(0, <module_name>);

    // Your testbench code here
end
```

It will create a `waveform.vcd` file in the `rfnoc-<module_name>/fpga/<module_name>/rfnoc_block_<block_name>/xsim_proj/xsim_proj.sim/sim_1/behav/xsim`directory.
You can then open it with GTKWave or any other VCD viewer.

## Description of the FPGA Image core

The YAML file inside the `icore` directory contains the description of the FPGA image that will be build and flashed on the USRP device.
You can specify the different blocks that should be added, static connection between them, and the transport adapters that should be used.
Please refer to the [RFNoC specification](https://files.ettus.com/app_notes/RFNoC_Specification.pdf) for more information on how to
create a YAML file for the image core, and the RFNoC architecture.

## References

- [RFNoC specification](https://files.ettus.com/app_notes/RFNoC_Specification.pdf)
- [UHD documentation](https://files.ettus.com/manual/)
- [Getting Started with RFNoC in UHD 4.0](https://kb.ettus.com/Getting_Started_with_RFNoC_in_UHD_4.0)
- [RFNoC Gain example](https://github.com/EttusResearch/uhd/tree/master/host/examples/rfnoc-gain)
