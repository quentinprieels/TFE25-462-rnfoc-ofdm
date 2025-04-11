module complex_trunc #(
    parameter integer WIDTH_IN = 41,
    parameter integer WIDTH_OUT = 16
)(
    input clk, input reset, input clear,

    // Input signals
    input [2*WIDTH_IN-1:0] i_tdata,
    input i_tlast,
    input i_tvalid,
    output i_tready,

    // Output signals (delayed & synchronized input)
    output [2*WIDTH_OUT-1:0] o_tdata,
    output o_tlast,
    output o_tvalid,
    input o_tready
);

wire [WIDTH_IN-1:0] i_tdata_real, i_tdata_imag;
wire [WIDTH_OUT-1:0] o_tdata_real, o_tdata_imag;

// Get the I/Q components from the input data
assign i_tdata_real = i_tdata[2*WIDTH_IN-1:WIDTH_IN];
assign i_tdata_imag = i_tdata[WIDTH_IN-1:0];

// Output the truncated I/Q components
assign o_tdata_real = i_tdata_real[WIDTH_IN-1:WIDTH_IN-WIDTH_OUT];
assign o_tdata_imag = i_tdata_imag[WIDTH_IN-1:WIDTH_IN-WIDTH_OUT];
assign o_tdata = {o_tdata_real, o_tdata_imag};

assign o_tlast = i_tlast;
assign o_tvalid = i_tvalid;
assign i_tready = o_tready;

endmodule // complex_trunc