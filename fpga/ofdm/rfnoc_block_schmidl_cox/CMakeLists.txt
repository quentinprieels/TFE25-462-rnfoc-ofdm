#
# Copyright 2025 <author>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# This macro will tell CMake that this directory contains an RFNoC block. It
# will parse Makefile.srcs to see which files need to be installed, and it will
# register a testbench target for this directory if desired.
RFNOC_REGISTER_BLOCK_DIR()
