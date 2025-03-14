//
// Copyright 2025 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

// Include our own header:
#include <rfnoc/ofdm/schmidl_cox_block_control.hpp>

// These two includes are the minimum required to implement a block:
#include <uhd/rfnoc/defaults.hpp>
#include <uhd/rfnoc/registry.hpp>

using namespace rfnoc::ofdm;
using namespace uhd::rfnoc;

// Define register addresses here:
//const uint32_t schmidl_cox_block_control::REG_NAME = 0x1234;

class schmidl_cox_block_control_impl : public schmidl_cox_block_control
{
public:
    RFNOC_BLOCK_CONSTRUCTOR(schmidl_cox_block_control) {}


private:
};

UHD_RFNOC_BLOCK_REGISTER_DIRECT(
    schmidl_cox_block_control, 3240, "Schmidl_cox", CLOCK_KEY_GRAPH, "bus_clk");
