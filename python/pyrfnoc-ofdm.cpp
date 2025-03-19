//
// Copyright 2024 Ettus Research, a National Instruments Brand
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

// NOTE: Most of these includes, as well as the numpy support, are not required
// for rfnoc-ofdm, but are commonly required
#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

namespace py = pybind11;


// We need this hack because import_array() returns NULL
// for newer Python versions.
// This function is also necessary because it ensures access to the C API
// and removes a warning.
void* init_numpy()
{
    import_array();
    return NULL;
}
#include "schmidl_cox_block_control_python.hpp"
#include "schmidl_cox_block_control_python.hpp"

PYBIND11_MODULE(rfnoc_ofdm_python, m)
{
    // Initialize the numpy C API
    // (otherwise we will see segmentation faults)
    init_numpy();

    // uhd::rfnoc::python::export_noc_block_base(m);
        export_schmidl_cox_block_control(m);
    export_schmidl_cox_block_control(m);
}
