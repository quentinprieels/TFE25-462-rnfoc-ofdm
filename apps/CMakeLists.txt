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

# rx_to_file_multi_usrp
add_executable(rx_to_file_multi_usrp
   rx_to_file_multi_usrp.cpp
)
target_include_directories(
   rx_to_file_multi_usrp
   PRIVATE ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(rx_to_file_multi_usrp
   ${UHD_LIBRARIES}
   ${Boost_LIBRARIES}
   -Wl,--no-as-needed
   rfnoc-ofdm
)

# rx_to_file_graph.cpp
add_executable(rx_to_file_graph
   rx_to_file_graph.cpp
)
target_include_directories(
   rx_to_file_graph
   PRIVATE ${CMAKE_SOURCE_DIR}/include
)
target_link_libraries(rx_to_file_graph
   ${UHD_LIBRARIES}
   ${Boost_LIBRARIES}
   -Wl,--no-as-needed
   rfnoc-ofdm
)

#### Once it's built... ########################################################
## Typically you would install the apps into $PATH, which is what we do here.
install(
   TARGETS rx_to_file_multi_usrp rx_to_file_graph
   RUNTIME
   DESTINATION ${RUNTIME_DIR}
   COMPONENT apps
)
