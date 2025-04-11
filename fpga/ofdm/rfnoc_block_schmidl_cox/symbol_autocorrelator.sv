//
// Symbol autocorrelator
//
// This module implements the Schmidl-Cox autocorrelator for OFDM symbol synchronization.
// It computes the correlation metric P(d) for the Schmidl-Cox algorithm.
// P(d+1) = P(d) + I(d - HALF_FFT_SIZE)* x I(d) - I(d - FFT_SIZE)* x I(d - HALF_FFT_SIZE)
// where I(d) is the input signal, and x denotes complex multiplication.
//
// This module outputs the correlation metric P(d) and the delayed input signal y(d-L).
// Both outputs are delayed during the processing to ensure synchronization.
//
// Caracters:
// --> 8 samples delay
// --> 16 bits per component
// --> truncated from 42 bits/component to 16 bits/component
//

module symbol_autocorrelator #(
    parameter integer FFT_SIZE = 1024
) (
    // System signals
    input clk,
    input reset,
    input clear,

    // Input signals
    input [31:0] i_tdata,
    input i_tlast,
    input i_tvalid,
    output i_tready,

    // Output signals (delayed & synchronized input)
    output [31:0] o_tdata,
    output o_tlast,
    output o_tvalid,
    input o_tready,
    
    // Output metric (P in the Schmidl-Cox algorithm)
    output [31:0] p_tdata,
    output p_tlast,
    output p_tvalid,
    input p_tready
);

localparam integer HALF_FFT_SIZE = FFT_SIZE / 2;
localparam integer HALF_FFT_SIZE_WIDTH = $clog2(HALF_FFT_SIZE + 1);


// Signal flow management - split the input stream into two streams
wire [31:0] i_cpy0_tdata,  i_cpy1_tdata;
wire        i_cpy0_tlast,  i_cpy1_tlast;
wire        i_cpy0_tvalid, i_cpy1_tvalid;
wire        i_cpy0_tready, i_cpy1_tready;
split_stream_fifo #(
    .WIDTH(32),
    .ACTIVE_MASK(4'b0011)
) in_splitter (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(i_tdata),
    .i_tlast(i_tlast),
    .i_tvalid(i_tvalid),
    .i_tready(i_tready),

    .o0_tdata(i_cpy0_tdata),
    .o0_tlast(i_cpy0_tlast),
    .o0_tvalid(i_cpy0_tvalid),
    .o0_tready(i_cpy0_tready),

    .o1_tdata(i_cpy1_tdata),
    .o1_tlast(i_cpy1_tlast),
    .o1_tvalid(i_cpy1_tvalid),
    .o1_tready(i_cpy1_tready),

    .o2_tready(1'b0),
    .o3_tready(1'b0)
);


// Computational - delay the input stream by HALF_FFT_SIZE samples
wire [31:0] dely_tdata;
wire        dely_tlast, dely_tvalid, dely_tready;
delay_fifo #(
    .WIDTH(32),
    .MAX_LEN(HALF_FFT_SIZE)
) delay_half_fft (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),

    .i_tdata(i_cpy0_tdata),
    .i_tlast(i_cpy0_tlast),
    .i_tvalid(i_cpy0_tvalid),
    .i_tready(i_cpy0_tready),

    .o_tdata(dely_tdata),
    .o_tlast(dely_tlast),
    .o_tvalid(dely_tvalid),
    .o_tready(dely_tready)
);


// Signal flow management - split the delayed stream into two streams
wire [31:0] dely_cpy0_tdata, dely_cpy1_tdata;
wire        dely_cpy0_tlast, dely_cpy1_tlast;
wire        dely_cpy0_tvalid, dely_cpy1_tvalid;
wire        dely_cpy0_tready, dely_cpy1_tready;
split_stream_fifo #(
    .WIDTH(32),
    .ACTIVE_MASK(4'b0011)
) delay_splitter (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(dely_tdata),
    .i_tlast(dely_tlast),
    .i_tvalid(dely_tvalid),
    .i_tready(dely_tready),

    .o0_tdata(dely_cpy0_tdata),
    .o0_tlast(dely_cpy0_tlast),
    .o0_tvalid(dely_cpy0_tvalid),
    .o0_tready(dely_cpy0_tready),

    .o1_tdata(dely_cpy1_tdata),
    .o1_tlast(dely_cpy1_tlast),
    .o1_tvalid(dely_cpy1_tvalid),
    .o1_tready(dely_cpy1_tready),

    .o2_tready(1'b0),
    .o3_tready(1'b0)
);


// Computational - conjugate the delayed stream
wire [31:0] dely_conj_tdata;
wire        dely_conj_tlast, dely_conj_tvalid, dely_conj_tready;
conj #(
    .WIDTH(16)
) delay_conj (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(dely_cpy1_tdata),
    .i_tlast(dely_cpy1_tlast),
    .i_tvalid(dely_cpy1_tvalid),
    .i_tready(dely_cpy1_tready),

    .o_tdata(dely_conj_tdata),
    .o_tlast(dely_conj_tlast),
    .o_tvalid(dely_conj_tvalid),
    .o_tready(dely_conj_tready)
);


// Signal flow management - delay the input stream by 1 sample (synchronise delay and non-delay paths)
wire [31:0] i_lat_tdata;
wire        i_lat_tlast, i_lat_tvalid, i_lat_tready;
split_stream_fifo #(
    .WIDTH(32),
    .ACTIVE_MASK(4'b0001)
) in_latency (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(i_cpy1_tdata),
    .i_tlast(i_cpy1_tlast),
    .i_tvalid(i_cpy1_tvalid),
    .i_tready(i_cpy1_tready),

    .o0_tdata(i_lat_tdata),
    .o0_tlast(i_lat_tlast),
    .o0_tvalid(i_lat_tvalid),
    .o0_tready(i_lat_tready),

    .o1_tready(1'b0),
    .o2_tready(1'b0),
    .o3_tready(1'b0)
);


// Computational - multiply the conjugated delayed stream with the original stream
wire [63:0] mult_tdata;
wire        mult_tlast, mult_tvalid, mult_tready;
cmul cmult (
    .clk(clk),
    .reset(reset),

    .a_tdata(i_lat_tdata),
    .a_tlast(i_lat_tlast),
    .a_tvalid(i_lat_tvalid),
    .a_tready(i_lat_tready),

    .b_tdata(dely_conj_tdata),
    .b_tlast(dely_conj_tlast),
    .b_tvalid(dely_conj_tvalid),
    .b_tready(dely_conj_tready),

    .o_tdata(mult_tdata),
    .o_tlast(mult_tlast),
    .o_tvalid(mult_tvalid),
    .o_tready(mult_tready)
);


// Computational - compute the moving sum of the multiplied stream
wire [32+$clog2(HALF_FFT_SIZE+1)-1:0] p_i_unscaled_tdata, p_q_unscaled_tdata;
wire        p_unscaled_tlast, p_unscaled_tvalid, p_unscaled_tready;
moving_sum #(
    .WIDTH(32),
    .MAX_LEN(HALF_FFT_SIZE)
) i_sum (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),

    .i_tdata(mult_tdata[63:32]),
    .i_tlast(mult_tlast),
    .i_tvalid(mult_tvalid),
    .i_tready(mult_tready),

    .o_tdata(p_i_unscaled_tdata),
    .o_tlast(p_unscaled_tlast),
    .o_tvalid(p_unscaled_tvalid),
    .o_tready(p_unscaled_tready)
);

moving_sum #(
    .WIDTH(32),
    .MAX_LEN(HALF_FFT_SIZE)
) q_sum (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),

    .i_tdata(mult_tdata[31:0]),
    .i_tlast(mult_tlast),
    .i_tvalid(mult_tvalid),
    .i_tready(), // mult_tready is set by sum0

    .o_tdata(p_q_unscaled_tdata),
    .o_tlast(),
    .o_tvalid(),
    .o_tready(p_unscaled_tready)  // mult_tready is set by sum0
);


// Signal flow management - truncate the output stream to 16 bits/component
complex_trunc #(
    .WIDTH_IN(32+$clog2(HALF_FFT_SIZE+1)),
    .WIDTH_OUT(16)
) end_trunc (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata({p_i_unscaled_tdata, p_q_unscaled_tdata}),
    .i_tlast(p_unscaled_tlast),
    .i_tvalid(p_unscaled_tvalid),
    .i_tready(p_unscaled_tready),

    .o_tdata(p_tdata),
    .o_tlast(p_tlast),
    .o_tvalid(p_tvalid),
    .o_tready(p_tready)
);

// Signal flow management - delay the delayed stream by 8 sample (synchronise y(d-L) with P(d))
axis_shift_register #(
    .WIDTH(32),
    .DELAY(8)
) delay_latency (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    
    .s_axis_tdata(dely_cpy0_tdata),
    .s_axis_tlast(dely_cpy0_tlast),
    .s_axis_tvalid(dely_cpy0_tvalid),
    .s_axis_tready(dely_cpy0_tready),
    
    .m_axis_tdata(o_tdata),
    .m_axis_tlast(o_tlast),
    .m_axis_tvalid(o_tvalid),
    .m_axis_tready(o_tready)
);

endmodule // symbol_autocorrelator