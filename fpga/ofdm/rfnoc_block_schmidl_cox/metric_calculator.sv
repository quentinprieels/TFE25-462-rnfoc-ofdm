module metric_caclulator #(
    parameter int FFT_SIZE = 16
)(
    input clk, input reset, input clear,
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

localparam HALF_FFT_SIZE = FFT_SIZE / 2;

wire [31:0] n0_tdata,  n1_tdata,  n10_tdata,  n11_tdata,  n2_tdata,  n3_tdata,  n4_tdata;
wire        n0_tlast,  n1_tlast,  n10_tlast,  n11_tlast,  n2_tlast,  n3_tlast,  n4_tlast;
wire        n0_tvalid, n1_tvalid, n10_tvalid, n11_tvalid, n2_tvalid, n3_tvalid, n4_tvalid;
wire        n0_tready, n1_tready, n10_tready, n11_tready, n2_tready, n3_tready, n4_tready;

// Split the input stream into two streams => i -> n0, n1
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

// Delay the second stream by HALF_FFT_SIZE => n1 -> n10
delay_fifo #(
  .WIDTH(32), 
  .MAX_LEN(HALF_FFT_SIZE)
) delay0 (
  .clk(clk), .reset(reset), .clear(clear),
  .len(4'd8), // TODO: This should be HALF_FFT_SIZE
  .i_tdata(n1_tdata), .i_tlast(n1_tlast), .i_tvalid(n1_tvalid), .i_tready(n1_tready),
  .o_tdata(n10_tdata), .o_tlast(n10_tlast), .o_tvalid(n10_tvalid), .o_tready(n10_tready)
);

// Conjugate the second stream => n10 -> n11 = n10*
conj #(
  .WIDTH(16)
) conj0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(n10_tdata), .i_tlast(n10_tlast), .i_tvalid(n10_tvalid), .i_tready(n10_tready),
  .o_tdata(n11_tdata), .o_tlast(n11_tlast), .o_tvalid(n11_tvalid), .o_tready(n11_tready)
);


// Multiply the first stream by the conjugate of the second stream n2 = n0 * n11
wire [63:0] mult_tdata;
wire        mult_tlast, mult_tvalid, mult_tready;
cmul cmul0 (
  .clk(clk), .reset(reset),
  .a_tdata(n0_tdata), .a_tlast(n0_tlast), .a_tvalid(n0_tvalid), .a_tready(n0_tready),
  .b_tdata(n11_tdata), .b_tlast(n11_tlast), .b_tvalid(n11_tvalid), .b_tready(n11_tready),
  .o_tdata(mult_tdata), .o_tlast(mult_tlast), .o_tvalid(mult_tvalid), .o_tready(mult_tready)
);

axi_clip_complex #(
  .WIDTH_IN(32),
  .WIDTH_OUT(16)
) axi_clip_complex0 (
  .clk(clk), .reset(reset),
  .i_tdata(mult_tdata), .i_tlast(mult_tlast), .i_tvalid(mult_tvalid), .i_tready(mult_tready),
  .o_tdata(n2_tdata), .o_tlast(n2_tlast), .o_tvalid(n2_tvalid), .o_tready(n2_tready)
);

// Moving average of the product stream
wire [19:0] i_ma;
wire [19:0] q_ma;
assign n3_tdata = {i_ma[19:4], q_ma[19:4]};

moving_sum #(
  .MAX_LEN(HALF_FFT_SIZE),
  .WIDTH(16)
) moving_sum0_i (
  .clk(clk), .reset(reset), .clear(clear),
  .len(4'd8), // TODO: This should be HALF_FFT_SIZE
  .i_tdata(n2_tdata[31:16]), .i_tlast(n2_tlast), .i_tvalid(n2_tvalid), .i_tready(n2_tready),
  .o_tdata(i_ma), .o_tlast(n3_tlast), .o_tvalid(n3_tvalid), .o_tready(n3_tready)
);

moving_sum #(
  .MAX_LEN(HALF_FFT_SIZE),
  .WIDTH(16)
) moving_sum0_q (
  .clk(clk), .reset(reset), .clear(clear),
  .len(4'd8), // TODO: This should be HALF_FFT_SIZE
  .i_tdata(n2_tdata[15:0]), .i_tlast(n2_tlast), .i_tvalid(n2_tvalid), .i_tready(n2_tready),
  .o_tdata(q_ma), .o_tlast(), .o_tvalid(), .o_tready(n3_tready) // n3_tlast, n3_tvalid are assigned by moving_sum0_i
);

// Get the square magnitude of the product stream
complex_to_magsq #(
  .WIDTH(16)
) complex_to_magsq0 (
  .clk(clk), .reset(reset), .clear(clear),
  .i_tdata(n3_tdata), .i_tlast(n3_tlast), .i_tvalid(n3_tvalid), .i_tready(n3_tready),
  .o_tdata(n4_tdata), .o_tlast(n4_tlast), .o_tvalid(n4_tvalid), .o_tready(n4_tready)
);

// Connect the output stream to the output port
assign o_tdata  = n4_tdata;
assign o_tlast  = n4_tlast;
assign o_tvalid = n4_tvalid;
assign n4_tready = o_tready;

endmodule // my_module 