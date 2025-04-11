// +-------------------------------------------------------------------------+
// | Metric calculator for the Schmidl-Cox synchronization algorithm         |
// +-------------------------------------------------------------------------+
// | 1) METRIC CALCULATION
// | This module calculates the final metric used for detection in the       |
// | Schmidl-Cox synchronization algorithm.                                  |
// |                                                                         |
// | The delay path P(d) is calculating the half-OFDM symbol correlation     |
// | metric: P(d + 1) = P(d)                                                 |
// |                  + I(d - HALF_FFT_SIZE)* x I(d)                         |
// |                  - I(d - FFT_SIZE)* x I(d - HALF_FFT_SIZE)              |
// |                                                                         |
// | The energy path R(d) is calculating the half-OFDM symbol energy metric: |
// | R(d + 1) = R(d)                                                         |
// |          + |I(d)|^2                                                     |
// |          - |I(d - HALF_FFT_SIZE)|^2                                     |
// |                                                                         |
// | The metic M(d) is calculated as: M(d) = |P(d)|^2 / (R(d))^2             |
// |                                                                         |
// | The metric is then passed into a moving sum (to average its values)     |
// | over a window of size CP: N = SUM(M(d), CP)                             |
// |                                                                         |
// | 2) DETECTION                                                            |
// | this module instantiates a detection module that uses the metric M(d)   |
// | to detect the start of the OFDM symbol.                                 |
// +-------------------------------------------------------------------------+

module metric_caclulator #(
    parameter int FFT_SIZE = 1024,
    parameter int CP_SIZE = 128
)(
    input clk, input reset, input clear,
    input [31:0] threshold, input [31:0] packet_length,  // Threshold for detection and length of the packet
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

wire [31:0] yl_tdata;
wire yl_tlast, yl_tvalid, yl_tready;

symbol_autocorrelator #(
    .FFT_SIZE(FFT_SIZE)
) autocorrelator (
    .clk(clk), .reset(reset), .clear(clear),
    .i_tdata(i_tdata), .i_tlast(i_tlast), .i_tvalid(i_tvalid), .i_tready(i_tready),
    .o_tdata(yl_tdata), .o_tlast(yl_tlast), .o_tvalid(yl_tvalid), .o_tready(o_tready), // Fix it
    .p_tdata(o_tdata), .p_tlast(o_tlast), .p_tvalid(o_tvalid), .p_tready(o_tready)
);

endmodule // metric_calculator