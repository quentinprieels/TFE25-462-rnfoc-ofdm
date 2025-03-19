module metric_caclulator #(
    parameter int FFT_SIZE = 16
)(
    input clk, input reset, input clear,
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

localparam HALF_FFT_SIZE = FFT_SIZE / 2;
localparam HALF_FFT_SIZE_WIDTH = $clog2(HALF_FFT_SIZE + 1);

wire [31:0] n0_tdata,  n1_tdata,  n2_tdata,  n3_tdata,  n4_tdata,   n5_tdata,   n6_tdata,   n7_tdata,   n8_tdata,   n9_tdata,   n10_tdata,  n11_tdata,  n12_tdata;
wire        n0_tlast,  n1_tlast,  n2_tlast,  n3_tlast,  n4_tlast,   n5_tlast,   n6_tlast,   n7_tlast,   n8_tlast,   n9_tlast,   n10_tlast,  n11_tlast,  n12_tlast;
wire        n0_tvalid, n1_tvalid, n2_tvalid, n3_tvalid, n4_tvalid,  n5_tvalid,  n6_tvalid,  n7_tvalid,  n8_tvalid,  n9_tvalid,  n10_tvalid, n11_tvalid, n12_tvalid;
wire        n0_tready, n1_tready, n2_tready, n3_tready, n4_tready,  n5_tready,  n6_tready,  n7_tready,  n8_tready,  n9_tready,  n10_tready, n11_tready, n12_tready;

// Split the input stream into two streams
split_stream_fifo #(
  .WIDTH(32),
  .ACTIVE_MASK(4'b0011)
) spliter0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(i_tdata), .i_tlast(i_tlast), .i_tvalid(i_tvalid), .i_tready(i_tready),           // In: i    - t0
  .o0_tdata(n0_tdata), .o0_tlast(n0_tlast), .o0_tvalid(n0_tvalid), .o0_tready(n0_tready),   // Out: n0  - t0
  .o1_tdata(n1_tdata), .o1_tlast(n1_tlast), .o1_tvalid(n1_tvalid), .o1_tready(n1_tready),   // Out: n1  - t0
  .o2_tready(1'b0), .o3_tready(1'b0)
);

// Connect the output stream to the output port
assign o_tdata  = n1_tdata;
assign o_tlast  = n1_tlast;
assign o_tvalid = n1_tvalid;
assign n1_tready = o_tready;

endmodule // my_module 