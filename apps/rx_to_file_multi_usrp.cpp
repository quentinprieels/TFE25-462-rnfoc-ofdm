//
// File-based signal processing through RFNoC schmidl-cox block
//

#include <uhd/utils/thread.hpp>
#include <uhd/exception.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <rfnoc/ofdm/schmidl_cox_block_control.hpp>
#include <boost/program_options.hpp>
#include <boost/format.hpp>
#include <chrono>
#include <iostream>
#include <fstream>
#include <complex>
#include <ctime>
#include <vector>
#include <csignal>
#include <string>
#include <algorithm>

namespace po = boost::program_options;
using multi_usrp            = uhd::usrp::multi_usrp;
using vec_str               = std::vector<std::string>;
using vec_d                 = std::vector<double>;
using vec_size_t            = std::vector<size_t>;
using vec_complex_float     = std::vector<std::complex<float>>;
using vec_vec_complex_float = std::vector<vec_complex_float>;

void print_help(const po::options_description &desc) {
	std::cout << boost::format("UHD RX Multi Samples with Schimidl & Cox %s\n") % desc;
	std::cout <<
        "\tThis is a demonstration of how to receive data from a USRP with Schmidl & Cox synchronization.\n"
		"\tThe data path is: radio -> ddc -> schmidl_cox -> stream_endpoint.\n"
		"\n"
		"\tSpecify --subdev to select channels.\n"
		"\tEx: --subdev=\"0:A\" to get a single channel on Basic RX.\n"
		"\n"
		"\tSpecify --args to select motherboard.\n"
		"\tEx: --args=\"addr=192.168.10.2\""
		<< std::endl;
}

void verify_gpsdo_sync(const multi_usrp::sptr &usrp) {
	uhd::time_spec_t time_last_pps = usrp->get_time_last_pps();
	while (time_last_pps == usrp->get_time_last_pps()) {
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}

	// Sleep a little to make sure all devices have seen a PPS edge
	std::this_thread::sleep_for(std::chrono::milliseconds(200));

	// Compare times across all mboards
	bool all_matched = true;
	uhd::time_spec_t mboard0_time = usrp->get_time_last_pps(0);
	for (size_t mboard = 1; mboard < usrp->get_num_mboards(); ++mboard) {
		uhd::time_spec_t mboard_time = usrp->get_time_last_pps(mboard);
		if (mboard_time != mboard0_time) {
			all_matched = false;
			std::cerr << boost::format(
				"ERROR: Times are not aligned: USRP "
				"0=%0.9f, USRP %d=%0.9f\n")
				% mboard0_time.get_real_secs()
				% mboard
				% mboard_time.get_real_secs();
		}
	}
	if (all_matched) {
		std::cout << "SUCCESS: USRP times aligned\n";
	} else {
		std::cout << "ERROR: USRP times are not aligned\n";
		exit(EXIT_FAILURE);
	}
}

void sync_gpsdo(const multi_usrp::sptr &usrp) {
	for (size_t mboard = 0; mboard < usrp->get_num_mboards(); ++mboard) {
		usrp->set_clock_source("gpsdo", mboard);
		usrp->set_time_source("gpsdo", mboard);
		if (!usrp->get_mboard_sensor("ref_locked", mboard).to_bool()) {
			std::cerr << boost::format(
				"GPS ref not locked on board %zu\n") % mboard;
			exit(EXIT_FAILURE);
		}
		size_t num_failed = 0;
		while (!(usrp->get_mboard_sensor("gps_locked",mboard).to_bool())) {
			++num_failed;
			std::this_thread::sleep_for(std::chrono::seconds(2));
			if (num_failed > 100) {
				std::cerr << boost::format(
					"GPS not locked on board %zu."
					" Wait a few minutes and try again.\n")
					% mboard;
				exit(EXIT_FAILURE);
			}
		}
		uhd::time_spec_t gps_time = uhd::time_spec_t(
			int64_t(usrp->get_mboard_sensor(
				        "gps_time", mboard).to_int()));
		usrp->set_time_next_pps(gps_time + 1.0, mboard);
		std::this_thread::sleep_for(std::chrono::seconds(2));
	}
}

int UHD_SAFE_MAIN(int argc, char* argv[]) {

	uhd::set_thread_priority_safe();

	// Variables to be set by po
	std::string args, filename, sync_method;
	double seconds_betw_meas, seconds_in_future, rate;
	size_t total_num_samps, nbr_meas;
	vec_d rx_freq, rx_gain, rx_bw;
	vec_str rx_ant, ref, subdev;
	vec_size_t channels;
	uint32_t sc_threshold;
	uint32_t sc_packet_size;

	// Setup program options
	po::options_description desc("Allowed options");
	desc.add_options()
		("help", "Print this help message")
		("args", po::value<std::string>(&args)->default_value(""), "single uhd device address args")
		("filename", po::value<std::string>(&filename)->default_value("data/test"), "name of the file to write binary samples to (w/o the .dat)")
		("secs", po::value<double>(&seconds_betw_meas)->default_value(0), "number of seconds between measurements")
		("nbr_meas", po::value<size_t>(&nbr_meas)->default_value(1), "number of measurements to receive")
		("nsamps", po::value<size_t>(&total_num_samps)->default_value(10000), "total number of samples to receive")
		
		("rate", po::value<double>(&rate)->default_value(1e6), "rate of incoming samples")
		("rx_freq", po::value<vec_d>(&rx_freq)->default_value(vec_d{1e9}, "1e9")->multitoken(), "RX RF center frequency in Hz")
		("rx_gain", po::value<vec_d>(&rx_gain)->default_value(vec_d{0.}, "0.")->multitoken(), "RX gain for the RF chain")
		("rx_ant", po::value<vec_str>(&rx_ant)->default_value(vec_str{"RX2"}, "RX2")->multitoken(), "RX antenna selection")
		("rx_bw", po::value<vec_d>(&rx_bw)->multitoken(), "RX daughterboard IF filter bandwidth in Hz")
		("ref", po::value<vec_str>(&ref)->default_value(vec_str{"internal"}, "internal")->multitoken(), "synchronization method: internal, external, gpsdo")
		("subdev", po::value<vec_str>(&subdev)->default_value(vec_str{"A:0"}, "A:0")->multitoken(), "subdev spec")
		
		("dilv", "specify to disable inner-loop verbose")
		("channels", po::value<vec_size_t>(&channels)->default_value(vec_size_t{0}, "0")->multitoken(), "which channel(s) to use")
		("sync", po::value<std::string>(&sync_method)->default_value("internal"), "initial synchronization method: internal, external, gpsdo")
		("sc_threshold", po::value<uint32_t>(&sc_threshold), "Schmidl & Cox threshold")
		("sc_packet_size", po::value<uint32_t>(&sc_packet_size), "Schmidl & Cox packet size");
		;
	po::variables_map vm;
	po::store(po::parse_command_line(argc, argv, desc), vm);

	// Print the help message
	if (vm.count("help")) {
		print_help(desc);
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

	bool verbose = vm.count("dilv") == 0;


	// ================== //
	// START SYSTEM SETUP //
	// ================== //
	
	// Create the USRP device
	std::cout << std::endl;
	std::cout << boost::format("Creating the USRP device with: %s...\n") % args;
	multi_usrp::sptr usrp = multi_usrp::make(args);

	// Select the subdevice (make it first, channel mapping affects the other settings)
	if (subdev.size() == 1) {
		usrp->set_rx_subdev_spec(subdev[0], multi_usrp::ALL_MBOARDS);
	} else if (subdev.size() > 1) {
		for (size_t i = 0; i < subdev.size(); ++i)
			usrp->set_rx_subdev_spec(subdev[i], i);
	}
	std::cout << boost::format("Using device: %s\n") % usrp->get_pp_string();

	// Synchronize devices
	if (sync_method == "external") {
		// Use external PPS
		usrp->set_clock_source("external", multi_usrp::ALL_MBOARDS);
		usrp->set_time_source("external", multi_usrp::ALL_MBOARDS);
		usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));
	} else if (sync_method == "internal") {
		// Use internal → no synchronization, no PPS
		usrp->set_clock_source("internal", multi_usrp::ALL_MBOARDS);
		usrp->set_time_source("internal", multi_usrp::ALL_MBOARDS);
		usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));
	} else if (sync_method == "gpsdo") {
		// Use GPS for synchronization
		sync_gpsdo(usrp);
		verify_gpsdo_sync(usrp);
		uhd::sensor_value_t gps_info(usrp->get_mboard_sensor("gps_gpgga"));
		std::cout << boost::format(
			"gps_gppda_info:\n"
			"\tName: %s\n"
			"\tValue: %s\n"
			"\tUnit: %s\n"
			"\tType: %s\n"
			"\tConverted:%s\n")
			% gps_info.name
			% gps_info.value
			% gps_info.unit
			% gps_info.type
			% gps_info.to_pp_string();
	} else {
		std::cerr << "ERROR: Unknown synchronization method: " << sync_method << std::endl;
		std::cerr << desc << std::endl;
		return EXIT_FAILURE;
	}
	std::cout << "Sync done.\n";

	// Setting LO and PPS reference
	if (ref.size() == 1 && sync_method != ref[0]) {
		usrp->set_clock_source(ref[0], multi_usrp::ALL_MBOARDS);
		usrp->set_time_source(ref[0], multi_usrp::ALL_MBOARDS);
	} else if (ref.size() > 1) {
		for (size_t i = 0; i < ref.size(); ++i) {
			usrp->set_clock_source(ref[i], i);
			usrp->set_time_source(ref[i], i);
		}
	}
	std::cout << "Setting LO and PPS reference done.\n";

	std::this_thread::sleep_for(std::chrono::seconds(1));

	for (size_t mboard = 0; mboard < usrp->get_num_mboards(); ++mboard) {
		if (!(usrp->get_mboard_sensor("ref_locked", mboard).to_bool())) {
			std::cerr << boost::format("Reference clock not locked on board %zu\n") % mboard;
			return EXIT_FAILURE;
		}
		std::cout << boost::format("Actual clock source RX%d: %s\n") % mboard % usrp->get_clock_source(mboard);
		std::cout << boost::format("Actual time source RX%d: %s\n") % mboard % usrp->get_time_source(mboard);
	}

	// Set the RX sample rate (sets across all channels)
	std::cout << boost::format("Setting RX Rate: %f Msps...\n") % (rate / 1e6);
	usrp->set_rx_rate(rate, multi_usrp::ALL_CHANS);
	std::cout << boost::format("Actual RX Rate: %f Msps\n") % (usrp->get_rx_rate() / 1e6);

	const size_t num_chan = usrp->get_rx_num_channels();
	std::cout << "Number of channels: " << num_chan << "\n";

	// Set the RX center frequency
	if (rx_freq.size() == 1) {
		for (size_t i = 0; i < num_chan; ++i) {
			usrp->set_rx_freq(rx_freq[0], i);
		}
	} else if (rx_freq.size() > 1) {
		for (size_t i = 0; i < rx_freq.size(); ++i) {
			usrp->set_rx_freq(rx_freq[i], i);
		}
	}
	for (size_t i = 0; i < num_chan; ++i) {
		std::cout << boost::format("Actual RX%d Freq: %f MHz\n") % i % (usrp->get_rx_freq(i) / 1e6);
	}

	// Set the RX RF gain
	if (rx_gain.size() == 1) {
		for (size_t i = 0; i < num_chan; ++i) {
			usrp->set_rx_gain(rx_gain[0], i);
		}
	} else if (rx_gain.size() > 1) {
		for (size_t i = 0; i < rx_gain.size(); ++i) {
			usrp->set_rx_gain(rx_gain[i], i);
		}
	}
	for (size_t i = 0; i < num_chan; ++i) {
		std::cout << boost::format("Actual RX%d Gain: %f dB\n") % i % usrp->get_rx_gain(i);
	}

	// Set the RX IF filter bandwidth
	if (rx_bw.size() == 1) {
		for (size_t i = 0; i < num_chan; ++i) {
			usrp->set_rx_bandwidth(rx_bw[0], i);
		}
	} else if (rx_bw.size() > 1) {
		for (size_t i = 0; i < rx_bw.size(); ++i) {
			usrp->set_rx_bandwidth(rx_bw[i], i);
		}
	}
	for (size_t i = 0; i < num_chan; ++i) {
		std::cout << boost::format("Actual RX%d Bandwidth: %f MHz\n") % i % (usrp->get_rx_bandwidth(i) / 1e6);
	}

	// Set the antennas
	if (rx_ant.size() == 1) {
		for (size_t channel = 0; channel < num_chan; ++channel) {
			usrp->set_rx_antenna(rx_ant[0], channel);
		}
	} else if (rx_ant.size() > 1) {
		for (size_t channel = 0; channel < rx_ant.size(); ++channel) {
			usrp->set_rx_antenna(rx_ant[channel], channel);
		}
	}
	for (size_t channel = 0; channel < num_chan; ++channel) {
		std::cout << boost::format("Actual Antenna RX%d: %s\n") % channel % usrp->get_rx_antenna(channel);
	}

	// Configure the Schmidl & Cox block
	auto graph = uhd::rfnoc::rfnoc_graph::make(args);
	auto sc_blocks = graph->find_blocks<rfnoc::ofdm::schmidl_cox_block_control>("");
	if (sc_blocks.empty()) {
		std::cerr << "No Schmidl & Cox block found." << std::endl;
		return EXIT_FAILURE;
	}
	std::cout << "Found " << sc_blocks.size() << " Schmidl & Cox blocks on this device." << std::endl;

	// Get the first Schmidl & Cox block
	auto sc_block = graph->get_block<rfnoc::ofdm::schmidl_cox_block_control>(sc_blocks.front());
	if (!sc_block) {
		std::cerr << "ERROR: Failed to extract Schmidl & Cox block controller!" << std::endl;
		return EXIT_FAILURE;
	}

	// Set the Schmidl & Cox threshold
	if (vm.count("threshold")) {
        std::cout << "Setting Schmidl & Cox threshold to " << sc_threshold << "..." << std::endl;
        sc_block->set_threshold_value(sc_threshold);
        const uint32_t threshold_read = sc_block->get_threshold_value();
        if (threshold_read != sc_threshold) {
            std::cerr << "ERROR: Readback of Schmidl & Cox threshold value not working! "
                      << "Expected: " << sc_threshold << " Read: " << threshold_read << std::endl;
            return EXIT_FAILURE;
        } else {
            std::cout << "Schmidl & Cox threshold value read/write loopback successful!" << std::endl;
        }
    } else {
        uint32_t default_threshold = sc_block->get_threshold_value();
        std::cout << "Using default Schmidl & Cox threshold value: " << default_threshold 
              << " (0x" << std::hex << default_threshold << std::dec << ")" << std::endl;
    }

	// Set the Schmidl & Cox packet size
	if (vm.count("packet-size")) {
        std::cout << "Setting Schmidl & Cox packet size to " << sc_packet_size << "..." << std::endl;
        sc_block->set_packet_size(sc_packet_size);
        const uint32_t sc_packet_size_read = sc_block->get_packet_size();
        if (sc_packet_size_read != sc_packet_size) {
            std::cerr << "ERROR: Readback of Schmidl & Cox packet size not working! "
                      << "Expected: " << sc_packet_size << " Read: " << sc_packet_size_read << std::endl;
            return EXIT_FAILURE;
        } else {
            std::cout << "Schmidl & Cox packet size read/write loopback successful!" << std::endl;
        }
    } else {
        std::cout << "Using default Schmidl & Cox packet size: " << sc_block->get_packet_size() 
              << " (0x" << std::hex << sc_block->get_packet_size() << std::dec << ")" << std::endl;
    }

	// Allow for some setup time
	std::this_thread::sleep_for(std::chrono::seconds(1));

	// Create dataOutfile
	std::ofstream dataOutfile(filename + "_rx.dat", std::ofstream::binary);


	// ==================== //
	// START DATA RECEIVING //
	// ==================== //

	// Create a recieve stream linearly map channels (index0 = channel0, index1 = channel1, ...)
	uhd::stream_args_t stream_args("fc32", "sc16"); //complex float
	stream_args.channels = channels;
	uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

	// Setup streaming
	seconds_in_future = usrp->get_time_last_pps().get_real_secs() + seconds_betw_meas;

	// Meta-data will be filled in by recv()
	uhd::rx_metadata_t md;

	// Allocate buffers to receive with sample (one buffer per channel)
	const size_t samps_per_buff = total_num_samps;
	vec_vec_complex_float buffs(num_chan, vec_complex_float(samps_per_buff));

	// Create a vector of pointers to point to each of the channel buffers
	std::vector<std::complex<float> *> buff_ptrs;
	for (size_t i = 0; i < num_chan; ++i) {
		buff_ptrs.push_back(&buffs[i].front());
	}


	// =============================== //
	// LOOP OVER MULTIPLE MEASUREMENTS //
	// =============================== //

	clock_t start_time, end_time;
	double cpu_time_used = 0.0;
	start_time = clock();

	std::cout << "Measurement loop starting" << std::endl;

	// Initialize maximum absolute value of the measured I and Q samples for clipping checking
	float maxI = 0;
	float maxQ = 0;

	for (size_t i = 0; i < nbr_meas; ++i) {
		std::cout << std::endl;

		uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
		stream_cmd.num_samps = total_num_samps;
		stream_cmd.stream_now = false;
		stream_cmd.time_spec = uhd::time_spec_t(seconds_in_future);
		rx_stream->issue_stream_cmd(stream_cmd); //tells all channels to stream

		double timeout = seconds_in_future + seconds_betw_meas - 0.1; //timeout (delay before receive + padding)
		size_t num_acc_samps = 0; //number of accumulated samples

		std::cout << "First timeout value = " << std::to_string(timeout) << " s." << std::endl;

		while (num_acc_samps < total_num_samps) {
			// Receive a single packet
			size_t num_rx_samps = rx_stream->recv(
				buff_ptrs, samps_per_buff, md, timeout
			);

			// Use a smaller timeout for subsequent packets
			timeout = 0.1;

			// Handle errors (in a more controlled way)
			if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
				std::cout << "Timeout error" << std::endl;
				break;
			}
			if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
				std::cerr << "Reception error" << std::endl;
				continue;
			}

			if (verbose) std::cout << boost::format("Received packet: %u samples, %u full secs, %f frac secs")
				% num_rx_samps
				% md.time_spec.get_full_secs()
				% md.time_spec.get_frac_secs()
				<< std::endl;

			num_acc_samps += num_rx_samps;

			for (size_t j = 0; j < num_chan; ++j) {
				// Check the maximal absolute value of I and Q to detect clipping
				std::vector<float> I_vec(num_rx_samps);
				std::vector<float> Q_vec(num_rx_samps);
				
				// Extract the absolute value of I and Q from the RX buffer and put it in I_vec and Q_vec
				for (size_t k = 0; k < num_rx_samps; k++) { 
					I_vec[k] = std::abs(buffs[j][k].real());
					Q_vec[k] = std::abs(buffs[j][k].imag());
				}
				
				// Find the maximum absolute value of I and Q
				maxI = *std::max_element(I_vec.begin(), I_vec.end());
				maxQ = *std::max_element(Q_vec.begin(), Q_vec.end());
				std::cout << "Maximal I absolute value: " << std::to_string(maxI) << std::endl;
				std::cout << "Maximal Q absolute value: " << std::to_string(maxQ) << std::endl;
				if ( (maxI >= 0.99) || (maxQ > 0.99) ) {
					std::cout << "WARNING: CLIPPING in measurements. Lower the gain or attenuate more the TX-RX direct path!" << std::endl;
				}

				// Write the received samples to the output file
				dataOutfile.write(reinterpret_cast<const char*> (&buffs[j].front()), 
				(std::streamsize)(num_rx_samps*sizeof(std::complex<float>)));	
			}
		}
		
		if (num_acc_samps < total_num_samps) {
			std::cerr << "Receive timeout before all samples were received" << std::endl;
		}

		seconds_in_future += seconds_betw_meas;

		end_time = clock();
		cpu_time_used = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
		std::cout << std::endl << "Current measurement time = " << cpu_time_used << " s" << std::endl;
	}

	// Close the output file
	dataOutfile.close();
	std::cout << "Done! Processed " << total_num_samps << " samples." << std::endl;

	return EXIT_SUCCESS;
}