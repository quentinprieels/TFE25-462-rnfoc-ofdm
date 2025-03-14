#
# Copyright 2019 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Uncomment the following lines to add your own IP:
# IP gets installed as-is, we simply recursively copy the ip directory to
# wherever it's supposed to go.
#install(
#    DIRECTORY ip/
#    DESTINATION ${GATEWARE_PKG_DATA_DIR}/ip
#    COMPONENT gateware
#)

# Now call add_subdirectory() for every block subdir
#add_subdirectory(rfnoc_block_myblock)

add_subdirectory(rfnoc_block_schmidl_cox)
