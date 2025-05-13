#
# Copyright 2019 Ettus Research, a National Instruments Brand
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Edit this to add your own apps!

## This app needs Boost
set(BOOST_REQUIRED_COMPONENTS
   program_options
   system
)
if(MSVC)
   set(BOOST_ALL_DYN_LINK "${BOOST_ALL_DYN_LINK}" CACHE BOOL "boost enable dynamic linking")
   if(BOOST_ALL_DYN_LINK)
       add_definitions(-DBOOST_ALL_DYN_LINK) #setup boost auto-linking in msvc
   else(BOOST_ALL_DYN_LINK)
       set(BOOST_REQUIRED_COMPONENTS) #empty components list for static link
   endif(BOOST_ALL_DYN_LINK)
endif(MSVC)
find_package(Boost 1.65 REQUIRED ${BOOST_REQUIRED_COMPONENTS})

# rx_to_file.cpp
add_executable(rx_to_file
   rx_to_file.cpp
)
target_include_directories(
   rx_to_file
   PRIVATE ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(rx_to_file
   ${UHD_LIBRARIES}
   ${Boost_LIBRARIES}
   -Wl,--no-as-needed
   rfnoc-ofdm
)

# rx_to_file_fft.cpp
add_executable(rx_to_file_fft
   rx_to_file_fft.cpp
)
target_include_directories(
   rx_to_file_fft
   PRIVATE ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(rx_to_file_fft
   ${UHD_LIBRARIES}
   ${Boost_LIBRARIES}
   -Wl,--no-as-needed
   rfnoc-ofdm
)

# tx_waveforms_radar.cpp
add_executable(tx_waveforms_radar
   tx_waveforms_radar.cpp
)
target_include_directories(
   tx_waveforms_radar
   PRIVATE ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(tx_waveforms_radar
   ${UHD_LIBRARIES}
   ${Boost_LIBRARIES}
   -Wl,--no-as-needed
   -Wall -Wextra -Wshadow -Wpedantic -Wconversion -Wsign-conversion -std=c++11
)


#### Once it's built... ########################################################
## Typically you would install the apps into $PATH, which is what we do here.
install(
   TARGETS rx_to_file rx_to_file_fft tx_waveforms_radar
   RUNTIME
   DESTINATION ${RUNTIME_DIR}
   COMPONENT apps
)
