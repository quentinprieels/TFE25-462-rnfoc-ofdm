//
// Copyright 2025 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Module: rfnoc_block_schmidl_cox_tb
//
// Description: Testbench for the schmidl_cox RFNoC block.
//

`default_nettype none


module rfnoc_block_schmidl_cox_tb;

  `include "test_exec.svh"

  import PkgTestExec::*;
  import PkgChdrUtils::*;
  import PkgRfnocBlockCtrlBfm::*;
  import PkgRfnocItemUtils::*;

  //---------------------------------------------------------------------------
  // Testbench Configuration
  //---------------------------------------------------------------------------

  localparam [31:0] NOC_ID          = 32'h00000CA8;
  localparam [ 9:0] THIS_PORTID     = 10'h123;
  localparam int    CHDR_W          = 64;    // CHDR size in bits
  localparam int    MTU             = 10;    // Log2 of max transmission unit in CHDR words
  localparam int    NUM_PORTS_I     = 1;
  localparam int    NUM_PORTS_O     = 1;
  localparam int    ITEM_W          = 32;    // Sample size in bits
  localparam int    SPP             = 64;    // Samples per packet
  localparam int    PKT_SIZE_BYTES  = SPP * (ITEM_W/8);
  localparam int    STALL_PROB      = 25;    // Default BFM stall probability
  localparam real   CHDR_CLK_PER    = 5.0;   // 200 MHz
  localparam real   CTRL_CLK_PER    = 8.0;   // 125 MHz
  localparam real   CE_CLK_PER      = 4.0;   // 250 MHz

  //---------------------------------------------------------------------------
  // Clocks and Resets
  //---------------------------------------------------------------------------

  bit rfnoc_chdr_clk;
  bit rfnoc_ctrl_clk;
  bit ce_clk;

  sim_clock_gen #(CHDR_CLK_PER) rfnoc_chdr_clk_gen (.clk(rfnoc_chdr_clk), .rst());
  sim_clock_gen #(CTRL_CLK_PER) rfnoc_ctrl_clk_gen (.clk(rfnoc_ctrl_clk), .rst());
  sim_clock_gen #(CE_CLK_PER) ce_clk_gen (.clk(ce_clk), .rst());

  //---------------------------------------------------------------------------
  // Bus Functional Models
  //---------------------------------------------------------------------------

  // Backend Interface
  RfnocBackendIf backend (rfnoc_chdr_clk, rfnoc_ctrl_clk);

  // AXIS-Ctrl Interface
  AxiStreamIf #(32) m_ctrl (rfnoc_ctrl_clk, 1'b0);
  AxiStreamIf #(32) s_ctrl (rfnoc_ctrl_clk, 1'b0);

  // AXIS-CHDR Interfaces
  AxiStreamIf #(CHDR_W) m_chdr [NUM_PORTS_I] (rfnoc_chdr_clk, 1'b0);
  AxiStreamIf #(CHDR_W) s_chdr [NUM_PORTS_O] (rfnoc_chdr_clk, 1'b0);

  // Block Controller BFM
  RfnocBlockCtrlBfm #(CHDR_W, ITEM_W) blk_ctrl = new(backend, m_ctrl, s_ctrl);

  // CHDR word and item/sample data types
  typedef ChdrData #(CHDR_W, ITEM_W)::chdr_word_t chdr_word_t;
  typedef ChdrData #(CHDR_W, ITEM_W)::item_t      item_t;

  // Connect block controller to BFMs
  for (genvar i = 0; i < NUM_PORTS_I; i++) begin : gen_bfm_input_connections
    initial begin
      blk_ctrl.connect_master_data_port(i, m_chdr[i], PKT_SIZE_BYTES);
      blk_ctrl.set_master_stall_prob(i, STALL_PROB);
    end
  end
  for (genvar i = 0; i < NUM_PORTS_O; i++) begin : gen_bfm_output_connections
    initial begin
      blk_ctrl.connect_slave_data_port(i, s_chdr[i]);
      blk_ctrl.set_slave_stall_prob(i, STALL_PROB);
    end
  end

  //---------------------------------------------------------------------------
  // Device Under Test (DUT)
  //---------------------------------------------------------------------------

  // DUT Slave (Input) Port Signals
  logic [CHDR_W*NUM_PORTS_I-1:0] s_rfnoc_chdr_tdata;
  logic [       NUM_PORTS_I-1:0] s_rfnoc_chdr_tlast;
  logic [       NUM_PORTS_I-1:0] s_rfnoc_chdr_tvalid;
  logic [       NUM_PORTS_I-1:0] s_rfnoc_chdr_tready;

  // DUT Master (Output) Port Signals
  logic [CHDR_W*NUM_PORTS_O-1:0] m_rfnoc_chdr_tdata;
  logic [       NUM_PORTS_O-1:0] m_rfnoc_chdr_tlast;
  logic [       NUM_PORTS_O-1:0] m_rfnoc_chdr_tvalid;
  logic [       NUM_PORTS_O-1:0] m_rfnoc_chdr_tready;

  // Map the array of BFMs to a flat vector for the DUT connections
  for (genvar i = 0; i < NUM_PORTS_I; i++) begin : gen_dut_input_connections
    // Connect BFM master to DUT slave port
    assign s_rfnoc_chdr_tdata[CHDR_W*i+:CHDR_W] = m_chdr[i].tdata;
    assign s_rfnoc_chdr_tlast[i]                = m_chdr[i].tlast;
    assign s_rfnoc_chdr_tvalid[i]               = m_chdr[i].tvalid;
    assign m_chdr[i].tready                     = s_rfnoc_chdr_tready[i];
  end
  for (genvar i = 0; i < NUM_PORTS_O; i++) begin : gen_dut_output_connections
    // Connect BFM slave to DUT master port
    assign s_chdr[i].tdata        = m_rfnoc_chdr_tdata[CHDR_W*i+:CHDR_W];
    assign s_chdr[i].tlast        = m_rfnoc_chdr_tlast[i];
    assign s_chdr[i].tvalid       = m_rfnoc_chdr_tvalid[i];
    assign m_rfnoc_chdr_tready[i] = s_chdr[i].tready;
  end

  rfnoc_block_schmidl_cox #(
    .THIS_PORTID         (THIS_PORTID),
    .CHDR_W              (CHDR_W),
    .MTU                 (MTU)
  ) dut (
    .rfnoc_chdr_clk      (rfnoc_chdr_clk),
    .rfnoc_ctrl_clk      (rfnoc_ctrl_clk),
    .ce_clk              (ce_clk),
    .rfnoc_core_config   (backend.cfg),
    .rfnoc_core_status   (backend.sts),
    .s_rfnoc_chdr_tdata  (s_rfnoc_chdr_tdata),
    .s_rfnoc_chdr_tlast  (s_rfnoc_chdr_tlast),
    .s_rfnoc_chdr_tvalid (s_rfnoc_chdr_tvalid),
    .s_rfnoc_chdr_tready (s_rfnoc_chdr_tready),
    .m_rfnoc_chdr_tdata  (m_rfnoc_chdr_tdata),
    .m_rfnoc_chdr_tlast  (m_rfnoc_chdr_tlast),
    .m_rfnoc_chdr_tvalid (m_rfnoc_chdr_tvalid),
    .m_rfnoc_chdr_tready (m_rfnoc_chdr_tready),
    .s_rfnoc_ctrl_tdata  (m_ctrl.tdata),
    .s_rfnoc_ctrl_tlast  (m_ctrl.tlast),
    .s_rfnoc_ctrl_tvalid (m_ctrl.tvalid),
    .s_rfnoc_ctrl_tready (m_ctrl.tready),
    .m_rfnoc_ctrl_tdata  (s_ctrl.tdata),
    .m_rfnoc_ctrl_tlast  (s_ctrl.tlast),
    .m_rfnoc_ctrl_tvalid (s_ctrl.tvalid),
    .m_rfnoc_ctrl_tready (s_ctrl.tready)
  );

  //---------------------------------------------------------------------------
  // Main Test Process
  //---------------------------------------------------------------------------

  initial begin : tb_main
    // Dump VCD file for waveform debugging
    $dumpfile("rfnoc_block_schmidl_cox_tb.vcd");
    $dumpvars(0, rfnoc_block_schmidl_cox_tb);

    // Initialize the test exec object for this testbench
    test.start_tb("rfnoc_block_schmidl_cox_tb");

    // Start the BFMs running
    blk_ctrl.run();

    //--------------------------------
    // Reset
    //--------------------------------

    test.start_test("Flush block then reset it", 10us);
    blk_ctrl.flush_and_reset();
    test.end_test();

    //--------------------------------
    // Verify Block Info
    //--------------------------------

    test.start_test("Verify Block Info", 2us);
    `ASSERT_ERROR(blk_ctrl.get_noc_id() == NOC_ID, "Incorrect NOC_ID Value");
    `ASSERT_ERROR(blk_ctrl.get_num_data_i() == NUM_PORTS_I, "Incorrect NUM_DATA_I Value");
    `ASSERT_ERROR(blk_ctrl.get_num_data_o() == NUM_PORTS_O, "Incorrect NUM_DATA_O Value");
    `ASSERT_ERROR(blk_ctrl.get_mtu() == MTU, "Incorrect MTU Value");
    test.end_test();

    //--------------------------------
    // Test Sequences
    //--------------------------------

    // Send file to block
    begin
      item_t send_samples[$];
      item_t recv_samples[$];
      logic signed [15:0] i_sample, q_sample;
      int input_file, output_file, num_samples, status, packets_sent;
      real i_val, q_val;
      string input_filename, output_input_filename;
      bit end_of_file;

      test.start_test("Reading IQ samples from file and processing", 250us);
      
      // File containing IQ samples
      input_filename = "/export/home/usrpconfig/Documents/GitHub/TFE25-462/rfnoc-ofdm/tests/signal_K1024_CP128_CPp128_M1_N1_preambleBPSK_payloadQPSK_usrp_recv.txt";
      output_input_filename = "/export/home/usrpconfig/Documents/GitHub/TFE25-462/rfnoc-ofdm/tests/signal_K1024_CP128_CPp128_M1_N1_preambleBPSK_payloadQPSK_usrp_recv_out.txt";

      // Open the input file for reading
      input_file = $fopen(input_filename, "r");
      if (input_file == 0) begin
        `ASSERT_ERROR(0, $sformatf("Failed to open file %s", input_filename));
      end

      // Open the output file for writing
      output_file = $fopen(output_input_filename, "w");
      if (output_file == 0) begin
        `ASSERT_ERROR(0, $sformatf("Failed to open file %s", output_input_filename));
      end

      // Initialize variables
      num_samples = 0;
      packets_sent = 0;
      send_samples = {};
      end_of_file = 0;

      // Reand and process the file
      while (!end_of_file) begin
        // Read I value
        status = $fscanf(input_file, "%e", i_val);
        if (status != 1) begin
          end_of_file = 1;
        end else begin

          // Read Q value
          status = $fscanf(input_file, "%e", q_val);
          if (status != 1) begin
            $display("Warning: Found I sample without Q sample at end of file");
            q_val = 0.0;
            end_of_file = 1;
          end

          // Convert floating point to sc16 format (signed 16-bit integers)
          // Scale to use full range but avoid overflow
          i_sample = $signed($rtoi(i_val * 32767.0));
          q_sample = $signed($rtoi(q_val * 32767.0));
          send_samples.push_back({i_sample, q_sample});
          num_samples++;
        end

        // When we have SPP samples or reached end of file, send the packet
        if (send_samples.size() >= SPP || (end_of_file && send_samples.size() > 0)) begin
          // Pad with zeros if we don't have enough samples
          while (send_samples.size() < SPP) begin
            send_samples.push_back({16'(0), 16'(0)}); // Pad with zeros
          end

          // Send the packet
          $display("Sending packet %0d with %0d samples", packets_sent, send_samples.size());
          blk_ctrl.send_items(0, send_samples);

          // Wait for and receive the processed packet
          blk_ctrl.recv_items(0, recv_samples);

          // Process and validate the received samples
          `ASSERT_ERROR(recv_samples.size() == SPP,
            $sformatf("Received payload didn't match size of payload sent (expected %0d, got %0d)", SPP, recv_samples.size()));

          // Convert the received samples back to floating point and write to output file
          for (int i=0; i < recv_samples.size(); i++) begin
            real output_i, output_q;
            item_t sample_out;
            sample_out = recv_samples[i];

            // Convert back to floating point
            output_i = $signed(sample_out[31:16]) / 32767.0;
            output_q = $signed(sample_out[15:0]) / 32767.0;

            // Write to output file
            $fwrite(output_file, "%.16e\n", output_i);
            $fwrite(output_file, "%.16e\n", output_q);
          end
          
          // Prepare for next packet
          send_samples = {};
          packets_sent++;
        end
      end

      // Close the file
      $fclose(input_file);
      $fclose(output_file);

      $display("Processed %0d samples in %0d packets", num_samples, packets_sent);
      test.end_test();
    end

    //--------------------------------
    // Finish Up
    //--------------------------------

    // Display final statistics and results
    test.end_tb();
  end : tb_main

endmodule : rfnoc_block_schmidl_cox_tb


`default_nettype wire
