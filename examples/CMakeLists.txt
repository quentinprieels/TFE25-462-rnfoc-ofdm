#
# Copyright 2024 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

set(examples_sources_py
    # Insert your example sources here if you want them to be installed
)

# TODO: Properly shebang the Python files depending on platform

install(
    FILES ${examples_sources_py}
    DESTINATION ${UHD_PKG_DATA_DIR}/examples/rfnoc-ofdm
    COMPONENT examples
)

