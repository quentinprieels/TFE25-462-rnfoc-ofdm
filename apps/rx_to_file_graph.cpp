#include <uhd/utils/thread.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/graph_utils.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/rfnoc/defaults.hpp>
#include <uhd/rfnoc/mb_controller.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <rfnoc/ofdm/schmidl_cox_block_control.hpp>
#include <boost/program_options.hpp>
#include <boost/format.hpp>
#include <chrono>
#include <csignal>


namespace po = boost::program_options;

// Singnal handler
static bool stop_signal_called = false;
void sig_int_handler(int) {
    stop_signal_called = true;
}

// Function to receive samples and write to file
/*
template <typename samp_type>
void recv_to_file(uhd::rx_streamer::sptr rx_stream,
    const std::string& file,
    const size_t samps_per_buff,
    const double rx_rate,
    const unsigned long long num_requested_samples,
    double time_requested       = 0.0,
    bool bw_summary             = false,
    bool stats                  = false,
    bool enable_size_map        = false,
    bool continue_on_bad_packet = false) {
    unsigned long long num_total_samps = 0;

    uhd::rx_metadata_t md;
    std::vector<samp_type> buff(samps_per_buff);
    std::ofstream outfile;
    if (not file.empty()) {
        outfile.open(file.c_str(), std::ofstream::binary);
    }
    bool overflow_message = true;

    // setup streaming
    uhd::stream_cmd_t stream_cmd((num_requested_samples == 0)
                                     ? uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS
                                     : uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    stream_cmd.num_samps  = size_t(num_requested_samples);
    stream_cmd.stream_now = true;
    stream_cmd.time_spec  = uhd::time_spec_t();
    std::cout << "Issuing stream cmd" << std::endl;
    rx_stream->issue_stream_cmd(stream_cmd);

    const auto start_time = std::chrono::steady_clock::now();
    const auto stop_time = start_time + std::chrono::milliseconds(int64_t(1000 * time_requested));
    // Track time and samps between updating the BW summary
    auto last_update                     = start_time;
    unsigned long long last_update_samps = 0;

    typedef std::map<size_t, size_t> SizeMap;
    SizeMap mapSizes;

    // Run this loop until either time expired (if a duration was given), until
    // the requested number of samples were collected (if such a number was
    // given), or until Ctrl-C was pressed.
    while (not stop_signal_called
           and (num_requested_samples != num_total_samps or num_requested_samples == 0)
           and (time_requested == 0.0 or std::chrono::steady_clock::now() <= stop_time)) {
        const auto now = std::chrono::steady_clock::now();

        size_t num_rx_samps =
            rx_stream->recv(&buff.front(), buff.size(), md, 3.0, enable_size_map);

        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
            std::cout << "Timeout while streaming" << std::endl;
            break;
        }
        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW) {
            if (overflow_message) {
                overflow_message = false;
                std::cerr
                    << "Got an overflow indication. Please consider the following:\n"
                       "  Your write medium must sustain a rate of "
                    << (rx_rate * sizeof(samp_type) / 1e6)
                    << "MB/s.\n"
                       "  Dropped samples will not be written to the file.\n"
                       "  Please modify this example for your purposes.\n"
                       "  This message will not appear again.\n";
            }
            continue;
        }
        if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
            std::string error = std::string("Receiver error: ") + md.strerror();
            if (continue_on_bad_packet) {
                std::cerr << error << std::endl;
                continue;
            } else
                throw std::runtime_error(error);
        }

        if (enable_size_map) {
            SizeMap::iterator it = mapSizes.find(num_rx_samps);
            if (it == mapSizes.end())
                mapSizes[num_rx_samps] = 0;
            mapSizes[num_rx_samps] += 1;
        }

        num_total_samps += num_rx_samps;

        if (outfile.is_open()) {
            outfile.write((const char*)&buff.front(), num_rx_samps * sizeof(samp_type));
        }

        if (bw_summary) {
            last_update_samps += num_rx_samps;
            const auto time_since_last_update = now - last_update;
            if (time_since_last_update > std::chrono::seconds(UPDATE_INTERVAL)) {
                const double time_since_last_update_s =
                    std::chrono::duration<double>(time_since_last_update).count();
                const double rate = double(last_update_samps) / time_since_last_update_s;
                std::cout << "\t" << (rate / 1e6) << " MSps" << std::endl;
                last_update_samps = 0;
                last_update       = now;
            }
        }
    }
    const auto actual_stop_time = std::chrono::steady_clock::now();

    stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
    std::cout << "Issuing stop stream cmd" << std::endl;
    rx_stream->issue_stream_cmd(stream_cmd);

    // Run recv until nothing is left
    int num_post_samps = 0;
    do {
        num_post_samps = rx_stream->recv(&buff.front(), buff.size(), md, 3.0);
    } while (num_post_samps and md.error_code == uhd::rx_metadata_t::ERROR_CODE_NONE);

    if (outfile.is_open())
        outfile.close();

    if (stats) {
        std::cout << std::endl;

        const double actual_duration_seconds =
            std::chrono::duration<float>(actual_stop_time - start_time).count();

        std::cout << "Received " << num_total_samps << " samples in "
                  << actual_duration_seconds << " seconds" << std::endl;
        const double rate = (double)num_total_samps / actual_duration_seconds;
        std::cout << (rate / 1e6) << " MSps" << std::endl;

        if (enable_size_map) {
            std::cout << std::endl;
            std::cout << "Packet size map (bytes: count)" << std::endl;
            for (SizeMap::iterator it = mapSizes.begin(); it != mapSizes.end(); it++)
                std::cout << it->first << ":\t" << it->second << std::endl;
        }
    }
}
*/

// Function to check if a sensor is locked
typedef std::function<uhd::sensor_value_t(const std::string&)> get_sensor_fn_t;
bool check_locked_sensor(std::vector<std::string> sensor_names, const char* sensor_name, get_sensor_fn_t get_sensor_fn, double setup_time) {
    if (std::find(sensor_names.begin(), sensor_names.end(), sensor_name) == sensor_names.end()) {
        return false;
    }

    auto setup_timeout = std::chrono::steady_clock::now() + std::chrono::milliseconds(int64_t(setup_time * 1000));
    bool lock_detected = false;

    std::cout << "Waiting for \"" << sensor_name << "\": ";
    std::cout.flush();

    while (true) {
        if (lock_detected and (std::chrono::steady_clock::now() > setup_timeout)) {
            std::cout << " locked." << std::endl;
            break;
        }
        if (get_sensor_fn(sensor_name).to_bool()) {
            std::cout << "+";
            std::cout.flush();
            lock_detected = true;
        } else {
            if (std::chrono::steady_clock::now() > setup_timeout) {
                std::cout << std::endl;
                throw std::runtime_error(std::string("timed out waiting for consecutive locks on sensor \"") + sensor_name + "\"");
            }
            std::cout << "_";
            std::cout.flush();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::cout << std::endl;
    return true;
}

int UHD_SAFE_MAIN(int argc, char* argv[]) {

    // Set thread priority
    uhd::set_thread_priority_safe();


    /*******************
     * PROGRAM OPTIONS *
     *******************/

    // Variables to be set by po
    std::string args, file, format, ant, subdev, ref, streamargs;
    size_t total_num_samps, spb, spp, radio_id, radio_chan;
    double rate, freq, gain, bw, total_time, setup_time, lo_offset;
    uint32_t threshold, packet_size;

    // Setup the program options
    po::options_description desc("Allowed options");
    desc.add_options()
        ("help", "Print this help message")
        ("file", po::value<std::string>(&file)->default_value("usrp_samples.dat"), "name of the file to write binary samples to (w/o the .dat)")
        ("format", po::value<std::string>(&format)->default_value("sc16"), "File sample format: sc16, fc32, or fc64")
        ("duration", po::value<double>(&total_time)->default_value(0), "total number of seconds to receive")
        ("nsamps", po::value<size_t>(&total_num_samps)->default_value(0), "total number of samples to receive")
        ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")
        ("spp", po::value<size_t>(&spp), "samples per packet (on FPGA and wire)")
        ("streamargs", po::value<std::string>(&streamargs)->default_value(""), "stream args")

        ("args", po::value<std::string>(&args)->default_value(""), "USRP device address args")
        ("setup-time", po::value<double>(&setup_time)->default_value(1.0), "seconds of setup time")

        ("radio-id", po::value<size_t>(&radio_id)->default_value(0), "Radio ID to use (0 or 1).") //! Only radio 0 is supported right now
        ("radio-chan", po::value<size_t>(&radio_chan)->default_value(0), "Radio channel")         //! Only channel 0 is supported right now
        ("rate", po::value<double>(&rate)->default_value(1e6), "RX rate of the radio block")
        ("freq", po::value<double>(&freq)->default_value(0.0), "RX RF center frequency in Hz")
        ("gain", po::value<double>(&gain)->default_value(0.0), "RX gain for the RF chain")
        ("ant", po::value<std::string>(&ant)->default_value("RX2"), "RX antenna selection")
        ("bw", po::value<double>(&bw)->default_value(0.0), "RX analog frontend filter bandwidth in Hz")
        ("ref", po::value<std::string>(&ref)->default_value("internal"), "reference source (internal, external, gpsdo)")
        ("subdev", po::value<std::string>(&subdev)->default_value("A:0"), "subdev spec")

        ("threshold", po::value<uint32_t>(&threshold)->default_value(0), "Schmidl & Cox threshold")
        ("packet-size", po::value<uint32_t>(&packet_size)->default_value(0), "Schmidl & Cox packet size")
        
        ("skip-lo", "Skip checking LO lock status")
        ("lo-offset", po::value<double>(&lo_offset), "Offset for frontend LO in Hz (optional)")

        ("int-n", "tune USRP with integer-N tuning")
        ("progress", "periodically display short-term bandwidth")
        ("stats", "show average bandwidth on exit")
        ("sizemap", "track packet size and display breakdown on exit")
        ("null", "run without writing to file")
        ("continue", "don't abort on a bad packet")
    ;
    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);

    // Print the help message
    if (vm.count("help")) {
        std::cout << "UHD/RFNoC RX samples to file with Schmidl & Cox  " << desc << std::endl;
        std::cout << std::endl
                  << "This application streams data from a signle channel of a USRP "
                     "device to a file. The data path is: radio -> ddc -> schmidl_cox -> stream_endpoint.\n"
                  << std::endl;
        return EXIT_SUCCESS;
    }

    // Notify the program options
    try {
        po::notify(vm);
    } catch (const po::error &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        std::cerr << desc << std::endl;
        return EXIT_FAILURE;
    }

    bool bw_summary = vm.count("progress") > 0;
    bool stats = vm.count("stats") > 0;
    if (vm.count("null") > 0) {
        file = "";
    }
    bool enable_size_map = vm.count("sizemap") > 0;
    bool continue_on_bad_packet = vm.count("continue") > 0;

    if (enable_size_map) {
        std::cout << "Packet size tracking enabled - will only recv one packet at a time!"
                  << std::endl;
    }

    // Check the format
    if (format != "sc16" and format != "fc32" and format != "fc64") {
        std::cout << "Invalid sample format: " << format << std::endl;
        return EXIT_FAILURE;
    }
    if (format != "sc16") {
        std::cout << "Warning: Only sc16 format is supported by the Schmidl & Cox block. "
                     "The program may not work as expected." << std::endl;
    }


    /************************************
     * CREATE device and block controls *
     ************************************/
    std::cout << std::endl;
    std::cout << "Creating the RFNoC graph with args: " << args << std::endl;
    auto graph = uhd::rfnoc::rfnoc_graph::make(args);

    // Radio
    uhd::rfnoc::block_id_t radio_ctrl_id(0, "Radio", radio_id);
    auto radio_ctrl = graph->get_block<uhd::rfnoc::radio_control>(radio_ctrl_id);
    if (!radio_ctrl) {
        std::cerr << "ERROR: Failed to extract radio block controller!" << std::endl;
        return EXIT_FAILURE;
    } else {
        std::cout << "Using radio " << radio_id << ", channel " << radio_chan << std::endl;
    }

    // Create the block chain from the radio to the stream endpoint
    uhd::rfnoc::ddc_block_control::sptr ddc_ctrl;
    size_t ddc_chan = 0;
    rfnoc::ofdm::schmidl_cox_block_control::sptr schmidl_cox_ctrl;
    size_t schmidl_cox_chan = 0;
    uhd::rfnoc::block_id_t last_block_in_chain;
    size_t last_port_in_chain;
    

    // Connect everything and found Schmidl & Cox block
    {
        auto edges = uhd::rfnoc::get_block_chain(graph, radio_ctrl_id, radio_chan, true);
        last_block_in_chain = edges.back().src_blockid;
        last_port_in_chain  = edges.back().src_port;
        if (edges.size() > 1) {
            uhd::rfnoc::connect_through_blocks(graph,
                radio_ctrl_id,
                radio_chan,
                last_block_in_chain,
                last_port_in_chain);
            for (auto& edge : edges) {
                if (uhd::rfnoc::block_id_t(edge.dst_blockid).get_block_name() == "DDC") {
                    ddc_ctrl = graph->get_block<uhd::rfnoc::ddc_block_control>(edge.dst_blockid);
                    ddc_chan = edge.dst_port;
                } 
                if (uhd::rfnoc::block_id_t(edge.dst_blockid).get_block_name() == "schmidl_cox") {
                    schmidl_cox_ctrl = graph->get_block<rfnoc::ofdm::schmidl_cox_block_control>(edge.dst_blockid);
                    schmidl_cox_chan = edge.dst_port;
                }
            }
        } else {
            std::cerr << "ERROR: No blocks found in the chain!" << std::endl;
            return EXIT_FAILURE;
        }

        //! This code supposes that the Schmidl & Cox block is always after the DDC block,
        //! And that it is part of the static crossbar configuration.
        // Check if DDC block is found
        if (!ddc_ctrl) {
            std::cerr << "ERROR: No DDC block found!" << std::endl;
            return EXIT_FAILURE;
        }

        // Check if Schmidl & Cox block is found
        if (!schmidl_cox_ctrl) {
            std::cerr << "ERROR: No Schmidl & Cox block found!" << std::endl;
            return EXIT_FAILURE;
        }
    }


    /******************
     * Setup up radio *
     ******************/

    // Lock mboard clock
    if (vm.count("ref")) {
        std::cout << "Setting reference source to " << ref << "..." << std::endl;
        graph->get_mb_controller(0)->set_clock_source(ref);
        graph->get_mb_controller(0)->set_time_source(ref);
        std::cout << "Reference source set to " << graph->get_mb_controller(0)->get_clock_source() << std::endl << std::endl;
    }

    // Set the RX RF gain
    if (vm.count("gain")) {
        std::cout << "Setting RX gain to " << gain << " dB..." << std::endl;
        radio_ctrl->set_rx_gain(gain, radio_chan);
        std::cout << "Actual RX Gain: " << radio_ctrl->get_rx_gain(radio_chan) << " dB" << std::endl << std::endl;
    }

    // Set the RX IF filter bandwidth
    if (vm.count("bw")) {
        std::cout << "Requesting bandwidth to " << (bw / 1e6) << " MHz..." << std::endl;
        radio_ctrl->set_rx_bandwidth(bw, radio_chan);
        std::cout << "Actual RX Bandwidth: " << radio_ctrl->get_rx_bandwidth(radio_chan) / 1e6 << " MHz" << std::endl << std::endl;
    }

    // Set the RX antenna
    if (vm.count("ant")) {
        std::cout << "Setting RX antenna to " << ant << "..." << std::endl;
        radio_ctrl->set_rx_antenna(ant, radio_chan);
        std::cout << "Actual RX Antenna: " << radio_ctrl->get_rx_antenna(radio_chan) << std::endl << std::endl;
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(int64_t(1000 * setup_time)));

    // check Ref and LO Lock detect
    if (not vm.count("skip-lo")) {
        check_locked_sensor(
            radio_ctrl->get_rx_sensor_names(radio_chan),
            "lo_locked",
            [&](const std::string& sensor_name) { return radio_ctrl->get_rx_sensor(sensor_name, radio_chan); },
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

    // Set the sample per packet chunck size
    if (vm.count("spp")) {
        std::cout << "Requesting samples per packet of: " << spp << std::endl;
        radio_ctrl->set_property<int>("spp", spp, radio_chan);
        spp = radio_ctrl->get_property<int>("spp", radio_chan);
        std::cout << "Actual samples per packet = " << spp << std::endl;
    }


    /************************************************************************
     * Set up streaming
     ***********************************************************************/
    uhd::device_addr_t streamer_args(streamargs);

    // Create the receiver streamer
    uhd::stream_args_t stream_args(format, "sc16"); //TODO: Check this. What is the output format that will be written to the file?
    stream_args.args = streamer_args;
    std::cout << "Using streamer args: " << stream_args.args.to_string() << std::endl;
    auto rx_stream = graph->create_rx_streamer(1, stream_args);

    // Connect streamer to last block and commit the graph
    graph->connect(last_block_in_chain, last_port_in_chain, rx_stream, 0);
    graph->commit();
    std::cout << "Active connections:" << std::endl;
    for (auto& edge : graph->enumerate_active_connections()) {
        std::cout << "* " << edge.to_string() << std::endl;
    }


    /**********************************************************
     * Set up sampling rate and schmidl_cox block properties. *
     **********************************************************/

    // Set the center frequency
    if (vm.count("freq")) {
        std::cout << "Requesting RX Freq: " << (freq / 1e6) << " MHz..." << std::endl;
        uhd::tune_request_t tune_request(freq);

        if (vm.count("lo-offset")) {
            std::cout << boost::format("Setting RX LO Offset: %f MHz...") % (lo_offset / 1e6) << std::endl;
            tune_request = uhd::tune_request_t(freq, lo_offset);
        }

        if (vm.count("int-n")) {
            tune_request.args = uhd::device_addr_t("mode_n=integer");
        }

        auto tune_req_action = uhd::rfnoc::tune_request_action_info::make(tune_request);
        tune_req_action->tune_request = tune_request;
        rx_stream->post_input_action(tune_req_action, 0);

        std::cout << "Actual RX Freq: " << (radio_ctrl->get_rx_frequency(radio_chan) / 1e6) << " MHz" << std::endl << std::endl;
    }

    // Set the sample rate
    if (rate <= 0.0) {
        std::cerr << "Please specify a valid sample rate" << std::endl;
        return EXIT_FAILURE;
    }
    std::cout << "Requesting RX Rate: " << (rate / 1e6) << " MHz..." << std::endl;
    if (ddc_ctrl) {
        std::cout << "Setting rate on DDC block..." << std::endl;
        rate = ddc_ctrl->set_output_rate(rate, ddc_chan);
    } else {
        std::cout << "Setting rate on radio block..." << std::endl;
        rate = radio_ctrl->set_rate(rate);
    }
    std::cout << "Actual RX Rate: " << (rate / 1e6) << " MHz" << std::endl << std::endl;

    // Set the Schmidl & Cox threshold
    if (vm.count("threshold")) {
        std::cout << "Setting Schmidl & Cox threshold to " << threshold << "..." << std::endl;
        schmidl_cox_ctrl->set_threshold_value(threshold);
        const uint32_t threshold_read = schmidl_cox_ctrl->get_threshold_value();
        if (threshold_read != threshold) {
            std::cerr << "ERROR: Readback of Schmidl & Cox threshold value not working! "
                      << "Expected: " << threshold << " Read: " << threshold_read << std::endl;
            return EXIT_FAILURE;
        } else {
            std::cout << "Schmidl & Cox threshold value read/write loopback successful!" << std::endl;
        }
    }

    // Set the Schmidl & Cox packet size
    if (vm.count("packet-size")) {
        std::cout << "Setting Schmidl & Cox packet size to " << packet_size << "..." << std::endl;
        schmidl_cox_ctrl->set_packet_size(packet_size);
        const uint32_t packet_size_read = schmidl_cox_ctrl->get_packet_size();
        if (packet_size_read != packet_size) {
            std::cerr << "ERROR: Readback of Schmidl & Cox packet size not working! "
                      << "Expected: " << packet_size << " Read: " << packet_size_read << std::endl;
            return EXIT_FAILURE;
        } else {
            std::cout << "Schmidl & Cox packet size read/write loopback successful!" << std::endl;
        }
    }


    /************************
     * Start streaming data *
     ************************/
    if (total_num_samps == 0) {
        std::signal(SIGINT, &sig_int_handler);
        std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
    }

    /*
    #define recv_to_file_args() (   \
        rx_stream,                  \
        file,                       \
        spb,                        \
        rate,                       \
        total_num_samps,            \
        total_time,                 \
        bw_summary,                 \
        stats,                      \
        enable_size_map,            \
        continue_on_bad_packet      \
    )

    // recv to file
    if (format == "fc64")
        recv_to_file<std::complex<double>> recv_to_file_args();
    else if (format == "fc32")
        recv_to_file<std::complex<float>> recv_to_file_args();
    else if (format == "sc16")
        recv_to_file<std::complex<short>> recv_to_file_args();
    else
        throw std::runtime_error("Unknown data format: " + format);
    */

    // finished
    std::cout << std::endl << "Done!" << std::endl << std::endl;

    return EXIT_SUCCESS;
}