#
# Copyright 2019 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# List all header files here (UHD and GNU Radio)
install(
    FILES
    schmidl_cox_block_control.hpp
    schmidl_cox_block_control.hpp
    #my_block_control.hpp
    DESTINATION include/rfnoc/ofdm
    COMPONENT headers
)
