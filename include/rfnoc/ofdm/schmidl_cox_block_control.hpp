//
// Copyright 2025 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#pragma once

#include <uhd/config.hpp>
#include <uhd/rfnoc/noc_block_base.hpp>

#include <cstdint>

namespace rfnoc { namespace ofdm {

/*! Block controller: Describe me!
 */
class UHD_API schmidl_cox_block_control : public uhd::rfnoc::noc_block_base {
    public:
        RFNOC_DECLARE_BLOCK(schmidl_cox_block_control)

        static const std::string PROP_KEY_THRESHOLD;
        static const std::string PROP_KEY_PACKET_SIZE;
        static const std::string PROP_KEY_OUTPUT_SELECT;

        // List all registers here if you need to know their address in the block controller:
        static const uint32_t REG_THRESHOLD_VALUE;
        static const uint32_t REG_REG_PACKET_SIZE;
        static const uint32_t REG_OUTPUT_SELECT;

        /*! Set the threshold value
        */
        virtual void set_threshold(const uint32_t threshold) = 0;

        /*! Get the current threshold value (read it from the device)
        */
        virtual uint32_t get_threshold() = 0;

        /*! Set the packet size
        */
        virtual void set_packet_size(const uint32_t packet_size) = 0;

        /*! Get the current packet size (read it from the device)
        */
        virtual uint32_t get_packet_size() = 0;

        /*! Set the output select
        */
        virtual void set_output_select(const uint32_t output_select) = 0;

        /*! Get the current output select (read it from the device)
        */
        virtual uint32_t get_output_select() = 0;
};

}} // namespace rfnoc::gain
