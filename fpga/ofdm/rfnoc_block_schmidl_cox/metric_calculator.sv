/*
 * This module calculates the metric for the Schmidl-Cox synchronization algorithm.
 * The delay path P(d) is calculating the half-OFDM symbol correlation metric :
 * P(d + 1) = P(d) + I(d - HALF_FFT_SIZE)* x I(d) - I(d - FFT_SIZE)* x I(d - HALF_FFT_SIZE) *
 * The energy path R(d) is calculating the half-OFDM symbol energy metric :
 * R(d + 1) = R(d) + |I(d)|^2 - |I(d - HALF_FFT_SIZE)|^2
 * 
 * The `i_tdata` input stream expects a complex number in the format [I, Q], where
 * I and Q are 16-bit signed integers, such that the real part I is hold in the 16
 * most significant bits and the imaginary part Q is hold in the 16 least significant
 * bits.
 */
module metric_caclulator #(
    parameter int FFT_SIZE = 1024,
    parameter int CP_SIZE = 128
)(
    input clk, input reset, input clear,
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

localparam HALF_FFT_SIZE = FFT_SIZE / 2;
localparam HALF_FFT_SIZE_WIDTH = $clog2(HALF_FFT_SIZE + 1);
localparam CP_SIZE_WIDTH = $clog2(CP_SIZE + 1);

// Complex signals: I on [31:16], Q on [15:0]
wire [31:0] c0_tdata,  c1_tdata,  c2_tdata,  c3_tdata,                        c6_tdata,  c7_tdata,  c8_tdata,  c9_tdata,  c10_tdata;
wire [63:0]                                             c4_tdata,  c5_tdata;
wire        c0_tlast,  c1_tlast,  c2_tlast,  c3_tlast,  c4_tlast,  c5_tlast,  c6_tlast,  c7_tlast,  c8_tlast,  c9_tlast,  c10_tlast;
wire        c0_tvalid, c1_tvalid, c2_tvalid, c3_tvalid, c4_tvalid, c5_tvalid, c6_tvalid, c7_tvalid, c8_tvalid, c9_tvalid, c10_tvalid;
wire        c0_tready, c1_tready, c2_tready, c3_tready, c4_tready, c5_tready, c6_tready, c7_tready, c8_tready, c9_tready, c10_tready;

// Real signals
wire signed [31:0] r8_tdata,             r10_tdata,  r11_tdata,  r12_tdata,  r13_tdata;
wire signed [15:0]            r9_tdata;
wire               r8_tlast,  r9_tlast,  r10_tlast,  r11_tlast,  r12_tlast,  r13_tlast;
wire               r8_tvalid, r9_tvalid, r10_tvalid, r11_tvalid, r12_tvalid, r13_tvalid;
wire               r8_tready, r9_tready, r10_tready, r11_tready, r12_tready, r13_tready;



/* 
 * Split the input stream into two streams
 * Out0, Out1 = In
 *
 * In:   i        -- t0
 * Out0: c0 (= i) -- t0
 * Out1: c1 (= i) -- t0
 * Out2: c7 (= i) -- t0
 */
split_stream_fifo #(
  .WIDTH(32),
  .ACTIVE_MASK(4'b0111)
) spliter0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(i_tdata),   .i_tlast(i_tlast),   .i_tvalid(i_tvalid),   .i_tready(i_tready),
  .o0_tdata(c0_tdata), .o0_tlast(c0_tlast), .o0_tvalid(c0_tvalid), .o0_tready(c0_tready),
  .o1_tdata(c1_tdata), .o1_tlast(c1_tlast), .o1_tvalid(c1_tvalid), .o1_tready(c1_tready),
  .o2_tdata(c7_tdata), .o2_tlast(c7_tlast), .o2_tvalid(c7_tvalid), .o2_tready(c7_tready),
  .o3_tready(1'b0)
);



/****************************
 * Delay path - P(d) metric *
 ****************************/
/*
 * Delay the input stream by HALF_FFT_SIZE samples
 * Out = In[-HALF_FFT_SIZE]
 *
 * In:  c0        -- t0
 * Out: c2 (= c0) -- t1 (= t0 - HALF_FFT_SIZE)
 */
delay_fifo #(
  .WIDTH(32),
  .MAX_LEN(HALF_FFT_SIZE)
) delay0 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(c0_tdata), .i_tlast(c0_tlast), .i_tvalid(c0_tvalid), .i_tready(c0_tready),
  .o_tdata(c2_tdata), .o_tlast(c2_tlast), .o_tvalid(c2_tvalid), .o_tready(c2_tready)
);

split_stream_fifo #(
  .WIDTH(32),
  .ACTIVE_MASK(4'b0011)
) spliter1 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(c2_tdata),   .i_tlast(c2_tlast),  .i_tvalid(c2_tvalid),   .i_tready(c2_tready),
  .o0_tdata(c8_tdata),  .o0_tlast(c8_tlast), .o0_tvalid(c8_tvalid), .o0_tready(c8_tready),
  .o1_tdata(c9_tdata),  .o1_tlast(c9_tlast), .o1_tvalid(c9_tvalid), .o1_tready(c9_tready),
  .o2_tready(1'b0), .o3_tready(1'b0)
);


/*
 * Conjugate the delayed stream
 * Out = In*
 *
 * In:  c1         -- t1
 * Out: c2 (= c1*) -- t1
 */
conj #(
  .WIDTH(16)
) conj0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(c8_tdata), .i_tlast(c8_tlast), .i_tvalid(c8_tvalid), .i_tready(c8_tready),
  .o_tdata(c3_tdata), .o_tlast(c3_tlast), .o_tvalid(c3_tvalid), .o_tready(c3_tready)
);


/*
 * Multiply the delayed and conjugated stream with the input stream
 * Out = In0 * In1
 *
 * In0: c1                         -- t0
 * In1: c3 (= c1[-HALF_FFT_SIZE]*) -- t1
 * Out: c5 (= c1 * c2)             -- t0 => n4 clipped to 16 bits
 */
cmul cmul0 (
  .clk(clk), .reset(reset),
  .a_tdata(c1_tdata),    .a_tlast(c1_tlast), .a_tvalid(c1_tvalid), .a_tready(c1_tready),
  .b_tdata(c3_tdata),    .b_tlast(c3_tlast), .b_tvalid(c3_tvalid), .b_tready(c3_tready),
  .o_tdata(c4_tdata), .o_tlast(c4_tlast), .o_tvalid(c4_tvalid), .o_tready(c4_tready)
);


/*
 * Calculate the moving sum of the product stream over a window of HALF_FFT_SIZE samples
 * CAUTION: we need 2 moving sums, one for the real part and one for the imaginary part
 * Out = sum(In)
 *
 * In:  c4 (c4 clipped to 16 bits) -- t0
 * Out: c5 (c5_unscalled 16 MSB)   -- t0
 */
wire [32+$clog2(HALF_FFT_SIZE+1)-1:0] c5_i_unscaled, c5_q_unscaled;
assign c5_tdata = {c5_i_unscaled[32+$clog2(HALF_FFT_SIZE+1)-1:$clog2(HALF_FFT_SIZE+1)],  // keep only the 32 MSB
                   c5_q_unscaled[32+$clog2(HALF_FFT_SIZE+1)-1:$clog2(HALF_FFT_SIZE+1)]};
moving_sum #(
  .WIDTH(32),
  .MAX_LEN(HALF_FFT_SIZE)
) sum0 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(c4_tdata[63:32]), .i_tlast(c4_tlast), .i_tvalid(c4_tvalid), .i_tready(c4_tready),
  .o_tdata(c5_i_unscaled),   .o_tlast(c5_tlast), .o_tvalid(c5_tvalid), .o_tready(c5_tready)
);

moving_sum #(
  .WIDTH(32),
  .MAX_LEN(HALF_FFT_SIZE)
) sum1 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(c4_tdata[31:0]), .i_tlast(c4_tlast), .i_tvalid(c4_tvalid), .i_tready(),          // c4_tready is set by sum0
  .o_tdata(c5_q_unscaled),  .o_tlast(),         .o_tvalid(),          .o_tready(c5_tready)  // c5_tlast & nf_tvalid are set by sum0
);


// Truncate the output stream to 16 bits
assign c6_tdata[31:16] = c5_tdata[63:48];  // keep only the 16 MSB
assign c6_tdata[15:0]  = c5_tdata[31:16];  // keep only the 16 LSB
assign c6_tlast = c5_tlast;
assign c6_tvalid = c5_tvalid;
assign c5_tready = c6_tready;

// P(d) complex signal is in c6_tdata



/*****************************
 * Energy path - R(d) metric *
 *****************************/
/*
 * Calculate the magnitude squared of the input stream
 * Out = |In|^2
 *
 * In:  c7            -- t0
 * Out: r8 (= |c7|^2) -- t0
 */
complex_to_magsq #(
  .WIDTH(16)
) magsq0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(c7_tdata), .i_tlast(c7_tlast), .i_tvalid(c7_tvalid), .i_tready(c7_tready),
  .o_tdata(r8_tdata), .o_tlast(r8_tlast), .o_tvalid(r8_tvalid), .o_tready(r8_tready)
);


/*
 * Calculate the moving sum of the magnitude squared stream over a window of HALF_FFT_SIZE samples
 * Out = sum(|In|^2)
 *
 * In:  r8          -- t0
 * Out: r9_unscaled -- t0
 */
wire [32+$clog2(HALF_FFT_SIZE+1)-1:0] r9_unscaled;
assign r9_tdata = r9_unscaled[32+$clog2(HALF_FFT_SIZE+1)-1:32+$clog2(HALF_FFT_SIZE+1)-16];
moving_sum #(
  .WIDTH(32),
  .MAX_LEN(HALF_FFT_SIZE)
) sum2 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(r8_tdata),    .i_tlast(r8_tlast), .i_tvalid(r8_tvalid), .i_tready(r8_tready),
  .o_tdata(r9_unscaled), .o_tlast(r9_tlast), .o_tvalid(r9_tvalid), .o_tready(r9_tready)
);

// R(d) real signal is in r9_tdata



/***************************
 * Normalize - M(d) metric *
 ***************************/
/*
 * Square the magnitude of the complex delay path signal
 * Out = |In|^2
 *
 * In:  c2             -- t0
 * Out: r10 (= |c2|^2) -- t0
 */
complex_to_magsq #(
  .WIDTH(16)
) magsq1 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(c6_tdata),  .i_tlast(c6_tlast),  .i_tvalid(c6_tvalid),  .i_tready(c6_tready),
  .o_tdata(r10_tdata), .o_tlast(r10_tlast), .o_tvalid(r10_tvalid), .o_tready(r10_tready)
);


/*
 * Square the magnitude of the real energy path signal
 * Out = In^2
 *
 * In:  r9           -- t0
 * Out: r11 (= r9^2) -- t0
 * 
 * Note: this block has a latency of 3 cycles
 */
mult #(
  .WIDTH_A(16),
  .WIDTH_B(16),
  .WIDTH_P(32),
  .LATENCY(3)
) mult0 (
  .clk(clk), .reset(reset),
  .a_tdata(r9_tdata), .a_tlast(r9_tlast),  .a_tvalid(r9_tvalid),  .a_tready(r9_tready),
  .b_tdata(r9_tdata), .b_tlast(r9_tlast),  .b_tvalid(r9_tvalid),  .b_tready(r9_tready),
  .p_tdata(r11_tdata), .p_tlast(r11_tlast), .p_tvalid(r11_tvalid), .p_tready(r11_tready)
);


/*
 * Divide the correlation metric by the energy metric
 * Out = In0 / In1
 *
 * In0: r10 (= |c2|^2) -- t0
 * In1: r11 (= r9^2)    -- t0
 * Out: r12 (= r10 / r11) -- t0
 *
 * Note: use of the divide_int32 in-tree Xilinx IP core
 * Note: We need to buffer the input streams to avoid deadlocks (axi_fifo seems to be buggy)
 */
wire signed [31:0] r10_buffered_tdata;
wire               r10_buffered_tlast, r10_buffered_tvalid, r10_buffered_tready;
axi_fifo_short #(
  .WIDTH(33)
  //.SIZE(4 + 3)  // 4 samples + 3 samples of latency => compensate for the latency of the mult block
) buffer0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata({r10_tlast, r10_tdata}), .i_tvalid(r10_tvalid), .i_tready(r10_tready),
  .o_tdata({r10_buffered_tlast, r10_buffered_tdata}), .o_tvalid(r10_buffered_tvalid), .o_tready(r10_buffered_tready)
);

wire signed [31:0] r11_buffered_tdata;
wire               r11_buffered_tlast, r11_buffered_tvalid, r11_buffered_tready;
axi_fifo_short #(
  .WIDTH(33)
  //.SIZE(4)
) buffer1 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata({r11_tlast, r11_tdata}), .i_tvalid(r11_tvalid), .i_tready(r11_tready),
  .o_tdata({r11_buffered_tlast, r11_buffered_tdata}), .o_tvalid(r11_buffered_tvalid), .o_tready(r11_buffered_tready)
);

wire signed [63:0] r12_unscaled;
assign r12_tdata = r12_unscaled[63:32];  // keep only the 32 MSB (quotient), discard the 32 LSB (fractional)
wire signed [31:0] r11_buffered_safe_divisor;
assign r11_buffered_safe_divisor = (r11_buffered_tdata == 0) ? 1 : r11_buffered_tdata;  // avoid division by zero
divide_int32 divide0 (
  .aclk(clk), .aresetn(~reset),
  .s_axis_dividend_tdata(r10_buffered_tdata),       .s_axis_dividend_tlast(r10_buffered_tlast), 
  .s_axis_dividend_tvalid(r10_buffered_tvalid),     .s_axis_dividend_tready(r10_buffered_tready),
  .s_axis_divisor_tdata(r11_buffered_safe_divisor), .s_axis_divisor_tlast(r11_buffered_tlast), 
  .s_axis_divisor_tvalid(r11_buffered_tvalid),      .s_axis_divisor_tready(r11_buffered_tready),
  .m_axis_dout_tdata(r12_unscaled),                 .m_axis_dout_tlast(r12_tlast), 
  .m_axis_dout_tvalid(r12_tvalid),                  .m_axis_dout_tready(r12_tready),
  .m_axis_dout_tuser()
);

// M(d) real signal is in r12_tdata
// r[d-L] is hold in c9_tdata



/****************************
 * Mooving average on M(d)  *
 ****************************/
/*
 * Calculate the moving average of the M(d) signal over a window of CP samples
 * Out = sum(In)
 *
 * In:  r12          -- t0
 * Out: r13_unscaled -- t0
 */

wire [32+$clog2(CP_SIZE+1)-1:0] r13_unscaled;
// assign r13_tdata = r13_unscaled[32+$clog2(CP_SIZE+1)-1:$clog2(CP_SIZE+1)]; // keep only the 32 MSB
assign r13_tdata = r13_unscaled[32-1:0];  // keep only the 32 LSB
moving_sum #(
  .WIDTH(32),
  .MAX_LEN(CP_SIZE)
) sum3 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(CP_SIZE[CP_SIZE_WIDTH-1:0]),
  .i_tdata(r12_tdata),    .i_tlast(r12_tlast), .i_tvalid(r12_tvalid), .i_tready(r12_tready),
  .o_tdata(r13_unscaled), .o_tlast(r13_tlast), .o_tvalid(r13_tvalid), .o_tready(r13_tready)
);

detector #(
  .HALF_FFT_SIZE(HALF_FFT_SIZE),
  .HALPH_CP_SIZE(CP_SIZE / 2)
) detector0 (
  .clk(clk), .reset(reset), .clear(clear),
  .threshold(32'h00000200),  // TODO: set the threshold dynamically
  .packet_length(32'd2304),  // TODO: set the packet length dynamically
  .m_tdata(r13_tdata), .m_tlast(r13_tlast), .m_tvalid(r13_tvalid), .m_tready(r13_tready), // Metric input
  .i_tdata(c9_tdata),  .i_tlast(c9_tlast),  .i_tvalid(c9_tvalid),  .i_tready(c9_tready),  // Input signal
  .o_tdata(c10_tdata), .o_tlast(c10_tlast), .o_tvalid(c10_tvalid), .o_tready(c10_tready)  // Output signal
);

// Connect the output stream to the output port
assign o_tdata  = c10_tdata;
assign o_tlast  = c10_tlast;
assign o_tvalid = c10_tvalid;
assign c10_tready = o_tready;

endmodule // metric_calculator