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
const uint32_t schmidl_cox_block_control::REG_THRESHOLD_VALUE = 0x00;
const uint32_t schmidl_cox_block_control::REG_REG_PACKET_SIZE = 0x01;
const uint32_t schmidl_cox_block_control::REG_OUTPUT_SELECT = 0x02;

const std::string schmidl_cox_block_control::PROP_KEY_THRESHOLD = "threshold";
const std::string schmidl_cox_block_control::PROP_KEY_PACKET_SIZE = "packet_size";
const std::string schmidl_cox_block_control::PROP_KEY_OUTPUT_SELECT = "output_select";

constexpr uint32_t DEFAULT_THRESHOLD = 0x02000000;
constexpr uint32_t DEFAULT_PACKET_SIZE = 0x00002304;
constexpr uint32_t DEFAULT_OUTPUT_SELECT = 0x00000000;

class schmidl_cox_block_control_impl : public schmidl_cox_block_control
{
public:
    RFNOC_BLOCK_CONSTRUCTOR(schmidl_cox_block_control) {
        // Threshold
        register_property(&_threshold);
        add_property_resolver({&_threshold}, {&_threshold}, [this]() {
            if (_threshold.get() < 0x00000001) {
                _threshold.set(0x00000001);
            }
            regs().poke32(REG_THRESHOLD_VALUE, static_cast<uint32_t>(_threshold.get()));
        });
        set_threshold(0x02000000);

        // Packet size
        register_property(&_packet_size);
        add_property_resolver({&_packet_size}, {&_packet_size}, [this]() {
            if (_packet_size.get() < 0x00000001) {
                _packet_size.set(0x00000001);
            }
            regs().poke32(REG_REG_PACKET_SIZE, static_cast<uint32_t>(_packet_size.get()));
        });
        set_packet_size(0x00002304);

        // Output select
        register_property(&_output_select);
        add_property_resolver({&_output_select}, {&_output_select}, [this]() {
            if (_output_select.get() < 0x00000000) {
                _output_select.set(0x00000000);
            }
            regs().poke32(REG_OUTPUT_SELECT, static_cast<uint32_t>(_output_select.get()));
        });
        set_output_select(0x00000000);
    }

    // Threshold
    void set_threshold(const uint32_t threshold) {
        set_property<int>(PROP_KEY_THRESHOLD, static_cast<int>(threshold));
    }

    uint32_t get_threshold() {
        return static_cast<uint32_t>(get_property<int>(PROP_KEY_THRESHOLD));
    }


    // Packet size
    void set_packet_size(const uint32_t packet_size) {
        set_property<int>(PROP_KEY_PACKET_SIZE, static_cast<int>(packet_size));
    }

    uint32_t get_packet_size() {
        return static_cast<uint32_t>(get_property<int>(PROP_KEY_PACKET_SIZE));
    }

    // Output select
    void set_output_select(const uint32_t output_select) {
        set_property<int>(PROP_KEY_OUTPUT_SELECT, static_cast<int>(output_select));
    }
    uint32_t get_output_select() {
        return static_cast<uint32_t>(get_property<int>(PROP_KEY_OUTPUT_SELECT));
    }

private:
    // Note: We use int instead of uint32_t here so we can use the built-in automatic
    // casting from string to int.
    property_t<int> _threshold{PROP_KEY_THRESHOLD, DEFAULT_THRESHOLD, {res_source_info::USER}};
    property_t<int> _packet_size{PROP_KEY_PACKET_SIZE, DEFAULT_PACKET_SIZE, {res_source_info::USER}};
    property_t<int> _output_select{PROP_KEY_OUTPUT_SELECT, DEFAULT_OUTPUT_SELECT, {res_source_info::USER}};
};

UHD_RFNOC_BLOCK_REGISTER_DIRECT(
    schmidl_cox_block_control, 3240, "Schmidl_cox", CLOCK_KEY_GRAPH, "bus_clk");
