//
// Copyright 2025 <author>
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Module: rfnoc_block_schmidl_cox
//
// Description:
//
//   <Add block description here>
//
// Parameters:
//
//   THIS_PORTID : Control crossbar port to which this block is connected
//   CHDR_W      : AXIS-CHDR data bus width
//   MTU         : Maximum transmission unit (i.e., maximum packet size in
//                 CHDR words is 2**MTU).
//

`default_nettype none

module rfnoc_block_schmidl_cox #(
  parameter [9:0] THIS_PORTID     = 10'd0,
  parameter       CHDR_W          = 64,
  parameter [5:0] MTU             = 10
)(
  // RFNoC Framework Clocks and Resets
  input  wire                   rfnoc_chdr_clk,
  input  wire                   rfnoc_ctrl_clk,
  input  wire                   ce_clk,
  // RFNoC Backend Interface
  input  wire [511:0]           rfnoc_core_config,
  output wire [511:0]           rfnoc_core_status,
  // AXIS-CHDR Input Ports (from framework)
  input  wire [(1)*CHDR_W-1:0] s_rfnoc_chdr_tdata,
  input  wire [(1)-1:0]        s_rfnoc_chdr_tlast,
  input  wire [(1)-1:0]        s_rfnoc_chdr_tvalid,
  output wire [(1)-1:0]        s_rfnoc_chdr_tready,
  // AXIS-CHDR Output Ports (to framework)
  output wire [(1)*CHDR_W-1:0] m_rfnoc_chdr_tdata,
  output wire [(1)-1:0]        m_rfnoc_chdr_tlast,
  output wire [(1)-1:0]        m_rfnoc_chdr_tvalid,
  input  wire [(1)-1:0]        m_rfnoc_chdr_tready,
  // AXIS-Ctrl Input Port (from framework)
  input  wire [31:0]            s_rfnoc_ctrl_tdata,
  input  wire                   s_rfnoc_ctrl_tlast,
  input  wire                   s_rfnoc_ctrl_tvalid,
  output wire                   s_rfnoc_ctrl_tready,
  // AXIS-Ctrl Output Port (to framework)
  output wire [31:0]            m_rfnoc_ctrl_tdata,
  output wire                   m_rfnoc_ctrl_tlast,
  output wire                   m_rfnoc_ctrl_tvalid,
  input  wire                   m_rfnoc_ctrl_tready
);

  //---------------------------------------------------------------------------
  // Signal Declarations
  //---------------------------------------------------------------------------

  // Clocks and Resets
  wire               ctrlport_clk;
  wire               ctrlport_rst;
  wire               axis_data_clk;
  wire               axis_data_rst;
  // CtrlPort Master
  wire               m_ctrlport_req_wr;
  wire               m_ctrlport_req_rd;
  wire [19:0]        m_ctrlport_req_addr;
  wire [31:0]        m_ctrlport_req_data;
  reg                m_ctrlport_resp_ack;
  reg [31:0]         m_ctrlport_resp_data;
  // Data Stream to User Logic: in
  wire [32*1-1:0]    m_in_axis_tdata;
  wire [1-1:0]       m_in_axis_tkeep;
  wire               m_in_axis_tlast;
  wire               m_in_axis_tvalid;
  wire               m_in_axis_tready;
  wire [63:0]        m_in_axis_ttimestamp;
  wire               m_in_axis_thas_time;
  wire [15:0]        m_in_axis_tlength;
  wire               m_in_axis_teov;
  wire               m_in_axis_teob;
  // Data Stream from User Logic: out
  wire [32*1-1:0]    s_out_axis_tdata;
  wire [0:0]         s_out_axis_tkeep;
  wire               s_out_axis_tlast;
  wire               s_out_axis_tvalid;
  wire               s_out_axis_tready;
  logic [63:0]       s_out_axis_ttimestamp;
  logic              s_out_axis_thas_time;
  logic [15:0]       s_out_axis_tlength;
  logic              s_out_axis_teov;
  logic              s_out_axis_teob;

  //---------------------------------------------------------------------------
  // NoC Shell
  //---------------------------------------------------------------------------

  noc_shell_schmidl_cox #(
    .CHDR_W              (CHDR_W),
    .THIS_PORTID         (THIS_PORTID),
    .MTU                 (MTU)
  ) noc_shell_schmidl_cox_i (
    //---------------------
    // Framework Interface
    //---------------------

    // Clock Inputs
    .rfnoc_chdr_clk      (rfnoc_chdr_clk),
    .rfnoc_ctrl_clk      (rfnoc_ctrl_clk),
    .ce_clk              (ce_clk),
    // Reset Outputs
    .rfnoc_chdr_rst      (),
    .rfnoc_ctrl_rst      (),
    .ce_rst              (),
    // CHDR Input Ports  (from framework)
    .s_rfnoc_chdr_tdata  (s_rfnoc_chdr_tdata),
    .s_rfnoc_chdr_tlast  (s_rfnoc_chdr_tlast),
    .s_rfnoc_chdr_tvalid (s_rfnoc_chdr_tvalid),
    .s_rfnoc_chdr_tready (s_rfnoc_chdr_tready),
    // CHDR Output Ports (to framework)
    .m_rfnoc_chdr_tdata  (m_rfnoc_chdr_tdata),
    .m_rfnoc_chdr_tlast  (m_rfnoc_chdr_tlast),
    .m_rfnoc_chdr_tvalid (m_rfnoc_chdr_tvalid),
    .m_rfnoc_chdr_tready (m_rfnoc_chdr_tready),
    // AXIS-Ctrl Input Port (from framework)
    .s_rfnoc_ctrl_tdata  (s_rfnoc_ctrl_tdata),
    .s_rfnoc_ctrl_tlast  (s_rfnoc_ctrl_tlast),
    .s_rfnoc_ctrl_tvalid (s_rfnoc_ctrl_tvalid),
    .s_rfnoc_ctrl_tready (s_rfnoc_ctrl_tready),
    // AXIS-Ctrl Output Port (to framework)
    .m_rfnoc_ctrl_tdata  (m_rfnoc_ctrl_tdata),
    .m_rfnoc_ctrl_tlast  (m_rfnoc_ctrl_tlast),
    .m_rfnoc_ctrl_tvalid (m_rfnoc_ctrl_tvalid),
    .m_rfnoc_ctrl_tready (m_rfnoc_ctrl_tready),

    //---------------------
    // Client Interface
    //---------------------

    // CtrlPort Clock and Reset
    .ctrlport_clk              (ctrlport_clk),
    .ctrlport_rst              (ctrlport_rst),
    // CtrlPort Master
    .m_ctrlport_req_wr         (m_ctrlport_req_wr),
    .m_ctrlport_req_rd         (m_ctrlport_req_rd),
    .m_ctrlport_req_addr       (m_ctrlport_req_addr),
    .m_ctrlport_req_data       (m_ctrlport_req_data),
    .m_ctrlport_resp_ack       (m_ctrlport_resp_ack),
    .m_ctrlport_resp_data      (m_ctrlport_resp_data),

    // AXI-Stream Clock and Reset
    .axis_data_clk (axis_data_clk),
    .axis_data_rst (axis_data_rst),
    // Data Stream to User Logic: in
    .m_in_axis_tdata      (m_in_axis_tdata),
    .m_in_axis_tkeep      (m_in_axis_tkeep),
    .m_in_axis_tlast      (m_in_axis_tlast),
    .m_in_axis_tvalid     (m_in_axis_tvalid),
    .m_in_axis_tready     (m_in_axis_tready),
    .m_in_axis_ttimestamp (m_in_axis_ttimestamp),
    .m_in_axis_thas_time  (m_in_axis_thas_time),
    .m_in_axis_tlength    (m_in_axis_tlength),
    .m_in_axis_teov       (m_in_axis_teov),
    .m_in_axis_teob       (m_in_axis_teob),
    // Data Stream from User Logic: out
    .s_out_axis_tdata      (s_out_axis_tdata),
    .s_out_axis_tkeep      (s_out_axis_tkeep),
    .s_out_axis_tlast      (s_out_axis_tlast),
    .s_out_axis_tvalid     (s_out_axis_tvalid),
    .s_out_axis_tready     (s_out_axis_tready),
    .s_out_axis_ttimestamp (s_out_axis_ttimestamp),
    .s_out_axis_thas_time  (s_out_axis_thas_time),
    .s_out_axis_tlength    (s_out_axis_tlength),
    .s_out_axis_teov       (s_out_axis_teov),
    .s_out_axis_teob       (s_out_axis_teob),

    //---------------------------
    // RFNoC Backend Interface
    //---------------------------
    .rfnoc_core_config   (rfnoc_core_config),
    .rfnoc_core_status   (rfnoc_core_status)
  );

  //---------------------------------------------------------------------------
  // User Logic
  //---------------------------------------------------------------------------

  //-------------------------------------
  // Registers
  //-------------------------------------
  localparam REG_THRESHOLD_ADDR = 0;
  localparam REG_PACKET_SIZE_ADDR = 1;
  localparam REG_OUTPUT_SELECT_ADDR = 2;
  localparam logic [31:0] REG_THRESHOLD_DEFAULT = 32'h02000000;
  localparam logic [31:0] REG_PACKET_SIZE_DEFAULT = 32'd2304;
  localparam logic REG_OUTPUT_SELECT_DEFAULT = 2'b0;

  reg [31:0] threshold = REG_THRESHOLD_DEFAULT;
  reg [31:0] packet_size = REG_PACKET_SIZE_DEFAULT;
  reg [1:0]  output_select = REG_OUTPUT_SELECT_DEFAULT;

  always @(posedge ctrlport_clk) begin
    if (ctrlport_rst) begin
      threshold <= REG_THRESHOLD_DEFAULT;
      packet_size <= REG_PACKET_SIZE_DEFAULT;
      output_select <= REG_OUTPUT_SELECT_DEFAULT;
    end else begin
      // Default assignment
      m_ctrlport_resp_ack <= 0;

      // Handle read requests      
      if (m_ctrlport_req_rd) begin
        case (m_ctrlport_req_addr)
          REG_THRESHOLD_ADDR: begin
            m_ctrlport_resp_data <= threshold;
            m_ctrlport_resp_ack <= 1;
          end
          REG_PACKET_SIZE_ADDR: begin
            m_ctrlport_resp_data <= packet_size;
            m_ctrlport_resp_ack <= 1;
          end
          REG_OUTPUT_SELECT_ADDR: begin
            m_ctrlport_resp_data <= {31'b0, output_select};
            m_ctrlport_resp_ack <= 1;
          end
        endcase
      end

      // Handle write requests
      if (m_ctrlport_req_wr) begin
        case (m_ctrlport_req_addr)
          REG_THRESHOLD_ADDR: begin
            threshold <= m_ctrlport_req_data;
            m_ctrlport_resp_ack <= 1;
          end
          REG_PACKET_SIZE_ADDR: begin
            packet_size <= m_ctrlport_req_data;
            m_ctrlport_resp_ack <= 1;
          end
          REG_OUTPUT_SELECT_ADDR: begin
            output_select <= m_ctrlport_req_data[1:0];
            m_ctrlport_resp_ack <= 1;
          end
        endcase
      end
    end
  end

  //-------------------------------------
  // Signal Processing
  //-------------------------------------
  localparam int FFT_SIZE = 1024;
  localparam int CP_SIZE = 128;
  localparam int OVERSAMPLING = 4;

  wire [32+$clog2((CP_SIZE * OVERSAMPLING)+1)-1:0] m_tdata;
  wire m_tlast, m_tvalid, m_tready;
  wire [31:0] yl_tdata;
  wire yl_tlast, yl_tvalid, yl_tready;
  wire [15:0] packet_len;
  wire eob;
  metric_calculator # (
    .FFT_SIZE(FFT_SIZE * OVERSAMPLING),
    .CP_SIZE(CP_SIZE * OVERSAMPLING)  
  ) mc0 (
    .clk(axis_data_clk),
    .reset(axis_data_rst),  // Used to reset the module on device startup
    .clear(1'b0),           // Used to reset only internal states of the module (not software defined registers)

    // Input signal
    .i_tdata(m_in_axis_tdata),
    .i_tlast(m_in_axis_tlast),
    .i_tvalid(m_in_axis_tvalid),
    .i_tready(m_in_axis_tready),

    // Metric output
    .m_tdata(m_tdata),
    .m_tlast(m_tlast),
    .m_tvalid(m_tvalid),
    .m_tready(m_tready),

    // Output signal
    .o_tdata(yl_tdata),
    .o_tlast(yl_tlast),
    .o_tvalid(yl_tvalid),
    .o_tready(yl_tready)
  );

  detector #(
    .HALF_FFT_SIZE((FFT_SIZE * OVERSAMPLING) / 2),
    .HALPH_CP_SIZE((CP_SIZE * OVERSAMPLING) / 2),
    .M_TDATA_WIDTH(32+$clog2((CP_SIZE * OVERSAMPLING)+1))
  ) detector0 (
    .clk(axis_data_clk),
    .reset(axis_data_rst),
    .clear(1'b0),

    .threshold(threshold),
    .packet_length(packet_size),
    .output_select(output_select),

    // Metric input
    .m_tdata(m_tdata),
    .m_tlast(m_tlast), 
    .m_tvalid(m_tvalid),
    .m_tready(m_tready),

    // Input signal
    .i_tdata(yl_tdata),
    .i_tlast(yl_tlast),
    .i_tvalid(yl_tvalid),
    .i_tready(yl_tready),

    // Output signal
    .o_tdata(s_out_axis_tdata),
    .o_tlast(s_out_axis_tlast),
    .o_tvalid(s_out_axis_tvalid),
    .o_tready(s_out_axis_tready),

    .end_of_ofdm_packet(eob),
    .rfnoc_packet_length(packet_len)
  );

  // Only 1-sample per clock, so tkeep should always be asserted
  assign s_out_axis_tkeep = 1'b1;

  // Add latency to the axi control signals
  wire [63:0] out_ttimestamp;
  wire out_thas_time;
  wire [15:0] out_tlength;
  wire out_teov;
  wire out_teob;
  axi_latency #(
      .WIDTH(64+16+1+1+1),
      .DELAY(87 + 1)
  ) yl_latency (
      .clk(axis_data_clk),
      .reset(axis_data_rst),
      .clear(1'b0),
      
      .s_axis_tdata({
          m_in_axis_ttimestamp,
          m_in_axis_thas_time,
          m_in_axis_tlength,
          m_in_axis_teov,
          m_in_axis_teob
      }),
      .s_axis_tlast(1'b0),
      .s_axis_tvalid(1'b0),
      .s_axis_tready(),
      
      .m_axis_tdata({
          out_ttimestamp,
          out_thas_time,
          out_tlength,
          out_teov,
          out_teob
      }),
      .m_axis_tlast(),
      .m_axis_tvalid(),
      .m_axis_tready(s_out_axis_tready)
  );

  always_comb begin
    if (output_select == 2'b01 || output_select == 2'b10) begin
      s_out_axis_ttimestamp = out_ttimestamp;
      s_out_axis_thas_time = out_thas_time;
      s_out_axis_tlength = packet_len;
      s_out_axis_teov = eob;
      s_out_axis_teob = eob;
    end else begin
      s_out_axis_ttimestamp = out_ttimestamp;
      s_out_axis_thas_time = out_thas_time;
      s_out_axis_tlength = out_tlength;
      s_out_axis_teov = out_teov;
      s_out_axis_teob = out_teob;
    end
  end

endmodule // rfnoc_block_schmidl_cox


`default_nettype wire
