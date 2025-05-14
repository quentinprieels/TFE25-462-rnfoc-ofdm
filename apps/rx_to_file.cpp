//
// Flexible UHD RX app for USRP X310 with custom Schmidl & Cox RFNoC block
// Allows receiving raw DDC output or output after Schmidl & Cox block.
//

#include <uhd/utils/thread.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/usrp/multi_usrp.hpp> // Although using graph, some utils might be relevant
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc/fft_block_control.hpp>
#include <rfnoc/ofdm/schmidl_cox_block_control.hpp> // Ensure this path is correct for your OOT module
#include <boost/program_options.hpp>
#include <boost/format.hpp>
#include <iostream>
#include <fstream>
#include <complex>
#include <vector>
#include <thread>
#include <chrono>
#include <stdexcept> // For exceptions

namespace po = boost::program_options;
using vec_complex_float = std::vector<std::complex<float>>;
using vec_complex_int16 = std::vector<std::complex<int16_t>>;
using vec_int32 = std::vector<int32_t>;

// Function to check if a sensor is locked (optional but good practice)
typedef std::function<uhd::sensor_value_t(const std::string&)> get_sensor_fn_t;
bool check_locked_sensor(const std::vector<std::string>& sensor_names, const char* sensor_name, get_sensor_fn_t get_sensor_fn, double setup_time) {
    // Check if the sensor name is valid
    if (std::find(sensor_names.begin(), sensor_names.end(), sensor_name) == sensor_names.end()) {
        std::cerr << "Warning: Sensor '" << sensor_name << "' not found." << std::endl;
        return true;
    }

    auto setup_timeout = std::chrono::steady_clock::now() + std::chrono::milliseconds(int64_t(setup_time * 1000));
    bool lock_detected = false;

    std::cout << boost::format("Waiting for \"%s - %s\": ") % sensor_name % sensor_names[0];
    std::cout.flush();

    while (true) {
        if (lock_detected and (std::chrono::steady_clock::now() > setup_timeout)) {
            std::cout << " locked." << std::endl;
            break;
        }
        if (not lock_detected) {
            lock_detected = get_sensor_fn(sensor_name).to_bool();
        }
        if (std::chrono::steady_clock::now() > setup_timeout) {
            std::cout << " timed out." << std::endl;
            throw std::runtime_error(str(boost::format("timed out waiting for consecutive locks on sensor \"%s\"") % sensor_name));
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "." << std::flush;
    }
    return true;
}


int UHD_SAFE_MAIN(int argc, char* argv[]) {
    
    uhd::set_thread_priority_safe();



    //--------------------------------------------------------------------------
    // Command-line options
    //--------------------------------------------------------------------------

    // Variable to be set by po
    std::string args, filename, rx_ant, ref, datapath, format, cpu_format, wire_format, output_info;
    double rate, rx_freq, rx_gain, rx_bw, setup_time, seconds_betw_meas;
    size_t total_num_samps, nbr_meas;
    uint32_t sc_threshold = 0, sc_packet_size = 0, sc_output_select = 0, fft_length = 1024 * 4, fft_cp_length = 128 * 4, fileidx_start = 0;
    bool use_schmidl_cox = false, use_fft = false;

    po::options_description desc("Allowed options");
    desc.add_options()
        // General options
        ("help,h",        "Print help message")
        ("args",        po::value<std::string>(&args)->default_value(""),               "USRP device address args (e.g., type=x300,addr=192.168.10.2)")
        ("filename",    po::value<std::string>(&filename)->default_value("rx_samples"), "Output file name (no extension)")
        ("ref",         po::value<std::string>(&ref)->default_value("external"),        "Reference source (internal, external, gpsdo)")
        ("setup-time",  po::value<double>(&setup_time)->default_value(1.5),             "Setup time (s) for locks")
        ("skip-lo", "Skip checking LO lock status")

        // Radio
        ("rate",    po::value<double>(&rate)->default_value(200e6),             "Sample rate (Hz)")
        ("rx_freq", po::value<double>(&rx_freq)->default_value(3.2e9),          "RX center frequency (Hz)")
        ("rx_gain", po::value<double>(&rx_gain)->default_value(30),             "RX gain (dB)")
        ("rx_bw",   po::value<double>(&rx_bw)->default_value(160e6),            "RX bandwidth (Hz)")
        ("rx_ant",  po::value<std::string>(&rx_ant)->default_value("TX/RX"),    "RX antenna")
        // ("radio_src_port", po::value<size_t>(&radio_src_port)->default_value(0), "Radio radio_src_port index to use")

        // Measurement
        ("nsamps",      po::value<size_t>(&total_num_samps)->default_value(6912),   "Samples to receive per measurement")
        ("nbr_meas",    po::value<size_t>(&nbr_meas)->default_value(1),             "Number of measurements")
        ("secs",        po::value<double>(&seconds_betw_meas)->default_value(0.5),  "Seconds between measurements")
        ("fileidx_start", po::value<uint32_t>(&fileidx_start)->default_value(0),      "File index start (for multiple measurements)")
        
        // Datapath and format
        ("datapath",    po::value<std::string>(&datapath)->default_value("raw"),    "Datapath: 'raw' (radio->ddc->host) or 'schmidl_cox' (radio->ddc->sc->host) or 'schmidl_cox_fft (radio->ddc->sc->fft->host)'")
        ("format",      po::value<std::string>(&format)->default_value("sc16"),     "Output file sample format: sc16 or fc32 or int32")

        // Schmidl & Cox block parameters (only used if datapath=schmidl_cox or schmidl_cox_fft)
        ("sc_threshold",    po::value<uint32_t>(&sc_threshold)->default_value(0x00200000),  "Schmidl & Cox threshold value")
        ("sc_packet_size",  po::value<uint32_t>(&sc_packet_size)->default_value(2304),      "Schmidl & Cox packet size value")
        ("sc_output_select", po::value<uint32_t>(&sc_output_select)->default_value(0),      "Schmidl & Cox output select value (0b00: signal with 0, 0b01: valid signal, 0b10: metricMSB, 0b11: metricLSB)")

        // FFT block parameters (only used if datapath=schmidl_cox_fft)
        ("fft_length",    po::value<uint32_t>(&fft_length)->default_value(1024 * 4),   "FFT length")
        ("fft_cp_length", po::value<uint32_t>(&fft_cp_length)->default_value(128 * 4), "FFT cyclic prefix length")
    ;

    // Parse command-line options
    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
        if (vm.count("help")) {
            std::cout << "Flexible RFNoC RX to File Application\n" << desc << std::endl;
            return EXIT_SUCCESS; 
        }
        po::notify(vm);
    } catch (const std::exception& e) {
        std::cerr << "Error parsing command line options: " << e.what() << std::endl;
        std::cerr << desc << std::endl;
        return EXIT_FAILURE;
    }

    // Validate and set options
    use_schmidl_cox = (datapath == "schmidl_cox" || datapath == "schmidl_cox_fft");
    use_fft = (datapath == "schmidl_cox_fft");

    if (format != "sc16" && format != "fc32" && format != "int32") {
        std::cerr << "Error: Invalid output format '" << format << "'. Must be 'sc16' or 'fc32' or 'int32'." << std::endl;
        return EXIT_FAILURE;
    }
    if (sc_output_select == 3 && format != "int32") {
        std::cerr << "Error: Invalid output format '" << format << "' for Schmidl & Cox output select {3}. Must be 'int32'." << std::endl;
        return EXIT_FAILURE;
    }
    if (format == "int32" && sc_output_select <= 2) {
        std::cerr << "Error: Invalid output format '" << format << "' for Schmidl & Cox output select {0, 1, 2}. Must be 'sc16' or 'fc32'." << std::endl;
        return EXIT_FAILURE;
    }
    cpu_format = format;
    if (format == "int32") {
        cpu_format = "sc16"; // Use sc16 for int16 format (it will be converted later)
    }

    if (datapath == "raw") {
        output_info = "";
    } else {
        if (sc_output_select == 0b00) {
            output_info = "signal_with_zeros.";
        } else if (sc_output_select == 0b01) {
            output_info = "signal.";
        } else if (sc_output_select == 0b10) {
            output_info = "signal_detected_idx.";
        } else if (sc_output_select == 0b11) {
            output_info = "metricLSB.";
        } else {
            std::cerr << "Error: Invalid output select value: " << sc_output_select << std::endl;
            return EXIT_FAILURE;
        }
    }


    //--------------------------------------------------------------------------
    // Create RFNoC graph
    //--------------------------------------------------------------------------
    
    std::cout << "Creating RFNoC graph with args: " << args << std::endl;
    uhd::rfnoc::rfnoc_graph::sptr graph;
    graph = uhd::rfnoc::rfnoc_graph::make(args);



    //--------------------------------------------------------------------------
    // Find blocks
    //--------------------------------------------------------------------------
    std::cout << "Finding and configuring blocks..." << std::endl;

    // Radio control
    uhd::rfnoc::block_id_t radio_id(0, "Radio", 0);     // ? Use params from command line
    uhd::rfnoc::radio_control::sptr radio_ctrl;
    radio_ctrl = graph->get_block<uhd::rfnoc::radio_control>(radio_id);
    if (!radio_ctrl) {
        std::cerr << "Error: No radio control blocks found in the graph." << std::endl;
        return EXIT_FAILURE;
    }
    std::cout << "Using Radio: " << radio_ctrl->get_block_id().to_string() << std::endl;
    std::cout << "Radio block has " << radio_ctrl->get_num_input_ports() << " input ports and " 
              << radio_ctrl->get_num_output_ports() << " output ports." << std::endl;

    // DDC Control
    uhd::rfnoc::block_id_t ddc_id(0, "DDC", 0);         // ? Use params from command line
    uhd::rfnoc::ddc_block_control::sptr ddc_ctrl;
    ddc_ctrl = graph->get_block<uhd::rfnoc::ddc_block_control>(ddc_id);
    if (!ddc_ctrl) {
        std::cerr << "Error: No DDC Control blocks found in the graph." << std::endl;
        return EXIT_FAILURE;
    }
    std::cout << "Using DDC: " << ddc_ctrl->get_block_id().to_string() << std::endl;
    std::cout << "DDC block has " << ddc_ctrl->get_num_input_ports() << " input ports and " 
              << ddc_ctrl->get_num_output_ports() << " output ports." << std::endl;

    // Schmidl & Cox Control (only if needed)
    uhd::rfnoc::block_id_t sc_id(0, "Schmidl_cox", 0);  // ? Use params from command line
    rfnoc::ofdm::schmidl_cox_block_control::sptr sc_ctrl;
    if (use_schmidl_cox) {
        sc_ctrl = graph->get_block<rfnoc::ofdm::schmidl_cox_block_control>(sc_id);
        if (!sc_ctrl) {
            std::cerr << "Error: No Schmidl & Cox Control blocks found in the graph." << std::endl;
            return EXIT_FAILURE;
        }
        std::cout << "Using Schmidl & Cox: " << sc_ctrl->get_block_id().to_string() << std::endl;
    }

    // FFT Control (only if needed)
    uhd::rfnoc::block_id_t fft_id(0, "FFT", 0);  // ? Use params from command line
    uhd::rfnoc::fft_block_control::sptr fft_ctrl;
    if (use_fft) {
        fft_ctrl = graph->get_block<uhd::rfnoc::fft_block_control>(fft_id);
        if (!fft_ctrl) {
            std::cerr << "Error: No FFT Control blocks found in the graph." << std::endl;
            return EXIT_FAILURE;
        }
        std::cout << "Using FFT: " << fft_ctrl->get_block_id().to_string() << std::endl;
    }



    //--------------------------------------------------------------------------
    // Configure blocks
    //--------------------------------------------------------------------------

    // Set up Radio
    radio_ctrl->set_rate(rate);
    std::cout << boost::format("Actual RX Rate: %f Msps.") % (radio_ctrl->get_rate() / 1e6) << std::endl;

    radio_ctrl->set_rx_frequency(rx_freq, 0);
    std::cout << boost::format("Actual RX Freq: %f MHz.") % (radio_ctrl->get_rx_frequency(0) / 1e6) << std::endl;

    radio_ctrl->set_rx_gain(rx_gain, 0);
    std::cout << boost::format("Actual RX Gain: %f dB.") % radio_ctrl->get_rx_gain(0) << std::endl;

    radio_ctrl->set_rx_bandwidth(rx_bw, 0);
    std::cout << boost::format("Actual RX Bandwidth: %f MHz.") % (radio_ctrl->get_rx_bandwidth(0) / 1e6) << std::endl;
    
    radio_ctrl->set_rx_antenna(rx_ant, 0);
    std::cout << boost::format("Actual RX Antenna: %s.") % radio_ctrl->get_rx_antenna(0) << std::endl;

    // Set clock and time source
    graph->get_mb_controller()->set_clock_source(ref);
    std::cout << "Reference source set to: " << graph->get_mb_controller()->get_clock_source() << std::endl;
    graph->get_mb_controller()->set_time_source(ref);
    std::cout << "Time source set to: " << graph->get_mb_controller()->get_time_source() << std::endl;
    graph->synchronize_devices(uhd::time_spec_t(0.0), false);
    std::cout << "Synchronizing devices..." << std::endl;

    // Wait for locks
    if (not vm.count("skip-lo")) {
        std::cout << "Waiting for reference clock lock..." << std::endl;
        check_locked_sensor(
            radio_ctrl->get_rx_sensor_names(0),
            "lo_locked",
            [&](const std::string& sensor_name) { return radio_ctrl->get_rx_sensor(sensor_name, 0); },
            setup_time
        );

        if (ref == "external") {
            check_locked_sensor(
                graph->get_mb_controller(0)->get_sensor_names(),
                "ref_locked",
                [&](const std::string& sensor_name) {  return graph->get_mb_controller(0)->get_sensor(sensor_name); },
                setup_time
            );
        }
    }

    // Set Schmidl & Cox registers (if using that path)
    if (use_schmidl_cox) {
        // Threshold
        if (vm.count("sc_threshold")) {
            std::cout << boost::format("Setting SC Threshold: 0x%08X (%u)...") % sc_threshold % sc_threshold << std::endl;
            sc_ctrl->set_threshold(sc_threshold);
        }
        uint32_t read_thresh = sc_ctrl->get_threshold();
        std::cout << boost::format("Read back SC Threshold: 0x%08X (%u)") % read_thresh % read_thresh << std::endl;

        // Packet Size
        if (vm.count("sc_packet_size")) {
            std::cout << boost::format("Setting SC Packet Size: 0x%08X (%u)...") % sc_packet_size % sc_packet_size << std::endl;
            sc_ctrl->set_packet_size(sc_packet_size);
        }
        uint32_t read_packet_size = sc_ctrl->get_packet_size();
        std::cout << boost::format("Read back SC Packet Size: 0x%08X (%u)") % read_packet_size % read_packet_size << std::endl;

        // Output Select
        if (vm.count("sc_output_select")) {
            std::cout << boost::format("Setting SC Output Select: 0x%08X (%u)...") % sc_output_select % sc_output_select << std::endl;
            sc_ctrl->set_output_select(sc_output_select);
        }
        uint32_t read_output_select = sc_ctrl->get_output_select();
        std::cout << boost::format("Read back SC Output Select: 0x%08X (%u)") % read_output_select % read_output_select << std::endl;
    }

    // Set FFT parameters (if using that path)
    if (use_fft) {
        // FFT Length
        if (vm.count("fft_length")) {
            std::cout << boost::format("Setting FFT Length: %u...") % fft_length << std::endl;
            fft_ctrl->set_length(fft_length);
        }
        uint32_t read_fft_length = fft_ctrl->get_length();
        std::cout << boost::format("Read back FFT Length: %u") % read_fft_length << std::endl;

        // Cyclic Prefix Length
        if (vm.count("fft_cp_length")) {
            std::cout << boost::format("Setting FFT Cyclic Prefix Length: %u...") % fft_cp_length << std::endl;
            fft_ctrl->set_cp_removal_list(std::vector<uint32_t>{fft_cp_length});
        }
        uint32_t read_cp_length = fft_ctrl->get_cp_removal_list()[0];
        std::cout << boost::format("Read back FFT Cyclic Prefix Length: %u") % read_cp_length << std::endl;
    }


    // Allow settings to settle
    std::this_thread::sleep_for(std::chrono::milliseconds(int64_t(1000 * setup_time / 2.0)));



    //--------------------------------------------------------------------------
    // Build Datapath and Streamer
    //--------------------------------------------------------------------------

    std::cout << "Connecting datapath: " << datapath << std::endl;
    uhd::rfnoc::block_id_t stream_source_block_id;
    size_t stream_source_port = 0;                      // ? Use params from command line

    if (use_schmidl_cox) {
        // Connect: radio[0] -> ddc[0]
        std::cout << "Connecting " << radio_ctrl->get_block_id().to_string() << ":" << 0
                  << " -> " << ddc_ctrl->get_block_id().to_string() << ":" << 0 << std::endl;
        graph->connect(radio_ctrl->get_block_id(), 0, ddc_ctrl->get_block_id(), 0);

        // Connect: ddc[0] -> sc[0]
        std::cout << "Connecting " << ddc_ctrl->get_block_id().to_string() << ":" << 0
                  << " -> " << sc_ctrl->get_block_id().to_string() << ":0" << std::endl;
        graph->connect(ddc_ctrl->get_block_id(), 0, sc_ctrl->get_block_id(), 0);

        // Connect: sc[0] -> fft[0]
        if (use_fft) {
            std::cout << "Connecting " << sc_ctrl->get_block_id().to_string() << ":" << 0
                      << " -> " << fft_ctrl->get_block_id().to_string() << ":0" << std::endl;
            graph->connect(sc_ctrl->get_block_id(), 0, fft_ctrl->get_block_id(), 0);
            stream_source_block_id = fft_ctrl->get_block_id();
        } else {
            stream_source_block_id = sc_ctrl->get_block_id();
        }

        stream_source_port = 0;
    } else {
        // Connect: radio[0] -> ddc[0]
        std::cout << "Connecting " << radio_ctrl->get_block_id().to_string() << ":" << 0
                  << " -> " << ddc_ctrl->get_block_id().to_string() << ":" << 0 << std::endl;
        graph->connect(radio_ctrl->get_block_id(), 0, ddc_ctrl->get_block_id(), 0);
        
        stream_source_block_id = ddc_ctrl->get_block_id();
        stream_source_port = 0;
    }

    // Create Streamer
    std::cout << "Creating RX streamer for format " << cpu_format << " (wire: sc16)" << std::endl;
    uhd::stream_args_t stream_args(cpu_format, "sc16");
    uhd::rx_streamer::sptr rx_stream = graph->create_rx_streamer(1, stream_args);
    graph->connect(stream_source_block_id, stream_source_port, rx_stream, 0);
    
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Commit the graph
    std::cout << "Committing graph..." << std::endl;
    graph->commit();

    // Print active connections
    std::cout << "Active connections:" << std::endl;
    for (auto& edge : graph->enumerate_active_connections()) {
        std::cout << "  * " << edge.to_string() << std::endl;
    }
    std::cout << std::endl;
    std::cout << "Graph committed." << std::endl;


    
    //--------------------------------------------------------------------------
    // Receive Loop
    //--------------------------------------------------------------------------

    size_t total_samps_received = 0;
    uhd::rx_metadata_t md;
    float recv_timeout = 3.0f; // Timeout for recv call

    // Allocate buffer based on CPU format
    vec_complex_float buff_fc32;
    vec_complex_int16 buff_sc16;
    std::vector<void*> buffs;
    size_t samps_per_buff = sc_packet_size; // std::min((size_t)rx_stream->get_max_num_samps(), total_num_samps); // Use smaller of max or requested total
    std::cout << "Using buffer size: " << samps_per_buff << " samples." << std::endl;

    if (cpu_format == "fc32") {
        buff_fc32.resize(samps_per_buff);
        buffs.push_back(buff_fc32.data());
    } else { // sc16
        buff_sc16.resize(samps_per_buff);
        buffs.push_back(buff_sc16.data());
    }

    // Setup stream command (receive N samples)
    uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    stream_cmd.num_samps = total_num_samps;
    stream_cmd.stream_now = true; // Start immediately for the first measurement


    std::cout << "\nStarting receive loop for " << nbr_meas << " measurements..." << std::endl;
    for (size_t meas = 0; meas < nbr_meas; ++meas) {
        std::cout << "Measurement " << meas + 1 << "/" << nbr_meas << ":" << std::endl;

        // Create unique filename for each measurement
        std::string current_filename;
        if (nbr_meas > 1) {
            current_filename = filename + "_" + datapath + "_meas" + std::to_string(meas + fileidx_start + 1) + "." + output_info + format + ".dat";
        } else {
            current_filename = filename + "_" + datapath + "." + output_info + format + ".dat";
        }

        std::cout << "Opening output file: " << current_filename << std::endl;
        std::ofstream outfile(current_filename, std::ios::binary);
        if (!outfile) {
            std::cerr << "Error opening output file: " << current_filename << std::endl;
            return EXIT_FAILURE;
        }

        // Issue stream command for this measurement
        stream_cmd.time_spec = uhd::time_spec_t(); // Reset time spec for stream_now=true
        rx_stream->issue_stream_cmd(stream_cmd);
        std::cout << "Issued stream command for " << total_num_samps << " samples." << std::endl;

        size_t current_meas_samps = 0;
        while(current_meas_samps < total_num_samps) {
            size_t num_rx_samps = rx_stream->recv(buffs, samps_per_buff, md, recv_timeout);
            
            // Handle timeout and errors
            if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
                std::cerr << "RX error: " << md.strerror() << std::endl;
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
                    std::cerr << "Timeout waiting for samples. Check connection and configuration." << std::endl;
                    // Decide whether to break or continue
                    break;
                }
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW) {
                    std::cerr << "Overflow detected (O)." << std::endl;
                    // Continue receiving, but be aware data was lost
                } else {
                    // Handle other errors potentially more severely
                    break;
                }
            }
            
            // Write samples to file
            if (num_rx_samps > 0) {
                size_t samps_to_write = std::min(num_rx_samps, total_num_samps - current_meas_samps);
                if (format == "fc32") {
                    outfile.write(reinterpret_cast<const char*>(buff_fc32.data()), samps_to_write * sizeof(std::complex<float>));
                } else if (format == "sc16") {
                    outfile.write(reinterpret_cast<const char*>(buff_sc16.data()), samps_to_write * sizeof(std::complex<int16_t>));
                } else if (format == "int32") {
                    // Convert complex<int16_t> to int32_t by combining real and imaginary parts
                    std::vector<int32_t> int32_buff(samps_to_write);
                    for (size_t i = 0; i < samps_to_write; ++i) {
                        // Combine real (upper 16 bits) and imaginary (lower 16 bits) parts
                        int32_t real_part = static_cast<int32_t>(buff_sc16[i].real()) & 0xFFFF;
                        int32_t imag_part = static_cast<int32_t>(buff_sc16[i].imag()) & 0xFFFF;
                        int32_buff[i] = (real_part << 16) | imag_part;
                    }
                    outfile.write(reinterpret_cast<const char*>(int32_buff.data()), samps_to_write * sizeof(int32_t));
                } else {
                    std::cerr << "Error: Unsupported format for writing samples." << std::endl;
                    return EXIT_FAILURE;
                }
                current_meas_samps += samps_to_write;
                total_samps_received += samps_to_write; // Track overall total if needed
                // std::cout << "." << std::flush;         // Progress indicator
            }

            // End of measurement check
            if (md.end_of_burst and current_meas_samps < total_num_samps) {
                std::cout << "\nEnd of burst detected before receiving all samples." << std::endl;
                break; // Exit inner loop for this measurement
            }
            if (md.end_of_burst) {
                break; // Expected end of burst
            }
        }
        // Close the file for this measurement
        outfile.close();
        std::cout << "\nMeasurement " << meas + 1 << " finished. Received " << current_meas_samps << " samples. Saved to " << current_filename << std::endl;

        // Wait before next measurement (if applicable)
        if (meas + 1 < nbr_meas) {
            std::cout << "Waiting " << seconds_betw_meas << " seconds..." << std::endl;
            std::this_thread::sleep_for(std::chrono::duration<double>(seconds_betw_meas));
            stream_cmd.stream_now = true; // Ensure next measurement starts immediately after delay
        }
    }

    std::cout << "\nDone. Saved " << nbr_meas << " measurements to files." << std::endl;
    return EXIT_SUCCESS;
}
