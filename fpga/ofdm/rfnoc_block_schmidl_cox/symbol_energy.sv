//
// Symbol energy computation block
//
// This module computes the R(d) metric in the Schmidl-Cox algorithm.
// It takes the input signal and computes the energy on half the FFT size
// of the signal.
//

module symbol_energy #(
    parameter integer FFT_SIZE = 1024
)(
    // System signals
    input clk,
    input reset,
    input clear,

    // Input signals
    input [31:0] i_tdata,
    input i_tlast,
    input i_tvalid,
    output i_tready,
    
    // Output signals
    output [15:0] o_tdata,
    output o_tlast,
    output o_tvalid,
    input o_tready
);

localparam integer HALF_FFT_SIZE = FFT_SIZE / 2;
localparam integer HALF_FFT_SIZE_WIDTH = $clog2(HALF_FFT_SIZE + 1);

// Computationnal - compute the abs^2 of the input stream
wire [31:0] abs_tdata;
wire        abs_tlast, abs_tvalid, abs_tready;
complex_to_magsq #(
    .WIDTH(16)
) abs_sq (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(i_tdata),
    .i_tlast(i_tlast),
    .i_tvalid(i_tvalid),
    .i_tready(i_tready),

    .o_tdata(abs_tdata),
    .o_tlast(abs_tlast),
    .o_tvalid(abs_tvalid),
    .o_tready(abs_tready)
);


// Computationnal - compute the moving sum of the abs^2 stream
wire [32+$clog2(HALF_FFT_SIZE+1)-1:0] sum_unscaled_tdata;
wire        sum_unscaled_tlast, sum_unscaled_tvalid, sum_unscaled_tready;
moving_sum #(
    .WIDTH(32),
    .MAX_LEN(HALF_FFT_SIZE)
) sum (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    .len(HALF_FFT_SIZE[HALF_FFT_SIZE_WIDTH-1:0]),

    .i_tdata(abs_tdata),
    .i_tlast(abs_tlast),
    .i_tvalid(abs_tvalid),
    .i_tready(abs_tready),

    .o_tdata(sum_unscaled_tdata),
    .o_tlast(sum_unscaled_tlast),
    .o_tvalid(sum_unscaled_tvalid),
    .o_tready(sum_unscaled_tready)
);


// Signal flow management - truncate the output stream to 16 bits/component
assign o_tdata = sum_unscaled_tdata[32+$clog2(HALF_FFT_SIZE+1)-1:32+$clog2(HALF_FFT_SIZE+1)-16];
assign o_tlast = sum_unscaled_tlast;
assign o_tvalid = sum_unscaled_tvalid;
assign sum_unscaled_tready = o_tready;

endmodule // symbol_energy