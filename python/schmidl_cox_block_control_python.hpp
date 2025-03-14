//
// Copyright 2025 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#pragma once

#include <uhd/rfnoc/block_controller_factory_python.hpp>
#include <rfnoc/ofdm/schmidl_cox_block_control.hpp>

using namespace rfnoc::ofdm;

void export_schmidl_cox_block_control(py::module& m)
{
    py::class_<schmidl_cox_block_control, schmidl_cox_block_control::sptr>(m, "schmidl_cox_block_control")
        .def(py::init(
            &uhd::rfnoc::block_controller_factory<schmidl_cox_block_control>::make_from))

        ;
}
