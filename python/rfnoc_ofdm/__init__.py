#
# Copyright 2024 Ettus Research, a National Instruments Company
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""
rfnoc-ofdm: Example module for Python support of an RFNoC OOT Module
"""

# Import all bindings from C++
from . import rfnoc_ofdm_python as lib

# In UHD, we use CamelCase for names in Python, so we'll do the same here
#MyBlockControl = lib.my_block_control