#
# Copyright 2019 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Set up library
########################################################################
# List any C++ sources here. If there are no sources (e.g., because there
# is no block controller), then this directory will be skipped.
list(APPEND rfnoc_ofdm_sources
    schmidl_cox_block_control.cpp
    #my_block_control.cpp
)
if(NOT rfnoc_ofdm_sources)
    MESSAGE(STATUS "No C++ sources... skipping lib/")
    return()
endif()

########################################################################
# Setup the include and linker paths
########################################################################
include_directories(
    ${CMAKE_SOURCE_DIR}/lib
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_BINARY_DIR}/lib
    ${CMAKE_BINARY_DIR}/include
    ${UHD_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIR}
)

link_directories(
    ${Boost_LIBRARY_DIRS}
)

add_library(rfnoc-ofdm SHARED
    ${rfnoc_ofdm_sources}
)
target_link_libraries(rfnoc-ofdm
    ${UHD_LIBRARIES}
    ${Boost_LIBRARIES}
)
set_target_properties(rfnoc-ofdm
    PROPERTIES DEFINE_SYMBOL "rfnoc_ofdm_EXPORTS")

file(GENERATE OUTPUT ${CMAKE_BINARY_DIR}/lib/rfnoc-ofdm CONTENT "$<TARGET_FILE_NAME:rfnoc-ofdm>\n")

########################################################################
# Install built library files
########################################################################
install(TARGETS rfnoc-ofdm
    LIBRARY DESTINATION lib${LIB_SUFFIX} # .so/.dylib file
    ARCHIVE DESTINATION lib${LIB_SUFFIX} # .lib file
    RUNTIME DESTINATION bin              # .dll file
)
install(FILES
    ${CMAKE_BINARY_DIR}/lib/rfnoc-ofdm
    DESTINATION ${MODULES_D_DIR}
    COMPONENT libraries
)
