/*
 * This module calculates the metric for the Schmidl-Cox synchronization algorithm.
 * 
 * The `i_tdata` input stream expects a complex number in the format [I, Q], where
 * I and Q are 16-bit signed integers, such that the real part I is hold in the 16
 * most significant bits and the imaginary part Q is hold in the 16 least significant
 * bits.
 */
module metric_caclulator #(
    parameter int FFT_SIZE = 1024
)(
    input clk, input reset, input clear,
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

localparam HALF_FFT_SIZE = FFT_SIZE / 2;
localparam HALF_FFT_SIZE_WIDTH = $clog2(HALF_FFT_SIZE + 1);

wire [31:0] n0_tdata,  n1_tdata,  n2_tdata,  n3_tdata,              n5_tdata,   n6_tdata,   n7_tdata,   n8_tdata,   n9_tdata,   n10_tdata,  n11_tdata,  n12_tdata;
wire        n0_tlast,  n1_tlast,  n2_tlast,  n3_tlast,  n4_tlast,   n5_tlast,   n6_tlast,   n7_tlast,   n8_tlast,   n9_tlast,   n10_tlast,  n11_tlast,  n12_tlast;
wire        n0_tvalid, n1_tvalid, n2_tvalid, n3_tvalid, n4_tvalid,  n5_tvalid,  n6_tvalid,  n7_tvalid,  n8_tvalid,  n9_tvalid,  n10_tvalid, n11_tvalid, n12_tvalid;
wire        n0_tready, n1_tready, n2_tready, n3_tready, n4_tready,  n5_tready,  n6_tready,  n7_tready,  n8_tready,  n9_tready,  n10_tready, n11_tready, n12_tready;


/* 
 * Split the input stream into two streams
 * Out0, Out1 = In
 *
 * In:   i        -- t0
 * Out0: n0 (= i) -- t0
 * Out1: n1 (= i) -- t0
 */
split_stream_fifo #(
  .WIDTH(32),
  .ACTIVE_MASK(4'b0011)
) spliter0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(i_tdata), .i_tlast(i_tlast), .i_tvalid(i_tvalid), .i_tready(i_tready),
  .o0_tdata(n0_tdata), .o0_tlast(n0_tlast), .o0_tvalid(n0_tvalid), .o0_tready(n0_tready),
  .o1_tdata(n1_tdata), .o1_tlast(n1_tlast), .o1_tvalid(n1_tvalid), .o1_tready(n1_tready),
  .o2_tready(1'b0), .o3_tready(1'b0)
);


/*
 * Delay the input stream by HALF_FFT_SIZE samples
 * Out = In[-HALF_FFT_SIZE]
 *
 * In:  n0        -- t0
 * Out: n1 (= n0) -- t1 (= t0 - HALF_FFT_SIZE)
 */
delay_fifo #(
  .WIDTH(32),
  .MAX_LEN(HALF_FFT_SIZE)
) delay0 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(n0_tdata), .i_tlast(n0_tlast), .i_tvalid(n0_tvalid), .i_tready(n0_tready),
  .o_tdata(n2_tdata), .o_tlast(n2_tlast), .o_tvalid(n2_tvalid), .o_tready(n2_tready)
);


/*
 * Conjugate the delayed stream
 * Out = In*
 *
 * In:  n1         -- t1
 * Out: n2 (= n1*) -- t1
 */
conj #(
  .WIDTH(16)
) conj0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(n2_tdata), .i_tlast(n2_tlast), .i_tvalid(n2_tvalid), .i_tready(n2_tready),
  .o_tdata(n3_tdata), .o_tlast(n3_tlast), .o_tvalid(n3_tvalid), .o_tready(n3_tready)
);


/*
 * Multiply the delayed and conjugated stream with the input stream
 * Out = In0 * In1
 *
 * In0: n1                         -- t0
 * In1: n3 (= n1[-HALF_FFT_SIZE]*) -- t1
 * Out: n5 (= n1 * n2)             -- t0 => n4 clipped to 16 bits
 */
wire [63:0] n4_unscaled;
cmul cmul0 (
  .clk(clk), .reset(reset),
  .a_tdata(n1_tdata), .a_tlast(n1_tlast), .a_tvalid(n1_tvalid), .a_tready(n1_tready),
  .b_tdata(n3_tdata), .b_tlast(n3_tlast), .b_tvalid(n3_tvalid), .b_tready(n3_tready),
  .o_tdata(n4_unscaled), .o_tlast(n4_tlast), .o_tvalid(n4_tvalid), .o_tready(n4_tready)
);

// Clip the 32-bit product to 16 bits
axi_clip_complex #(
  .WIDTH_IN(32),
  .WIDTH_OUT(16)
) clip0 (
  .clk(clk), .reset(reset),
  .i_tdata(n4_unscaled), .i_tlast(n4_tlast), .i_tvalid(n4_tvalid), .i_tready(n4_tready),
  .o_tdata(n5_tdata), .o_tlast(n5_tlast), .o_tvalid(n5_tvalid), .o_tready(n5_tready)
);


/*
 * Calculate the moving sum of the product stream over a window of HALF_FFT_SIZE samples
 * CAUTION: we need 2 moving sums, one for the real part and one for the imaginary part
 * Out = sum(In)
 *
 * In:  n5_unscaled -- t0
 * Out: n6_unscaled -- t0
 */
wire [16+$clog2(HALF_FFT_SIZE+1)-1:0] n6_i_unscaled, n6_q_unscaled;
assign n6_tdata = {n6_i_unscaled[16+$clog2(HALF_FFT_SIZE+1)-1:$clog2(HALF_FFT_SIZE+1)],  // keep only the 16 MSB
                   n6_q_unscaled[16+$clog2(HALF_FFT_SIZE+1)-1:$clog2(HALF_FFT_SIZE+1)]};
moving_sum #(
  .WIDTH(16),
  .MAX_LEN(HALF_FFT_SIZE)
) sum0 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(n5_tdata[31:16]), .i_tlast(n5_tlast), .i_tvalid(n5_tvalid), .i_tready(n5_tready),
  .o_tdata(n6_i_unscaled), .o_tlast(n6_tlast), .o_tvalid(n6_tvalid), .o_tready(n6_tready)
);

moving_sum #(
  .WIDTH(16),
  .MAX_LEN(HALF_FFT_SIZE)
) sum1 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),
  .i_tdata(n5_tdata[15:0]), .i_tlast(n5_tlast), .i_tvalid(n5_tvalid), .i_tready(),  // n5_tready is set by sum0
  .o_tdata(n6_q_unscaled), .o_tlast(), .o_tvalid(), .o_tready(n6_tready)            // n6_tlast & nf_tvalid are set by sum0
);


// Connect the output stream to the output port
assign o_tdata  = n6_tdata;
assign o_tlast  = n6_tlast;
assign o_tvalid = n6_tvalid;
assign n6_tready = o_tready;

endmodule // my_module 