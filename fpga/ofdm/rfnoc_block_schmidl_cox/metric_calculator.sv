module metric_caclulator #(
    parameter int FFT_SIZE = 4
)(
    input clk, input reset, input clear,
    input [31:0] i_tdata, input i_tlast, input i_tvalid, output i_tready,   // Payload input stream
    output [31:0] o_tdata, output o_tlast, output o_tvalid, input o_tready  // Payload output stream
);

localparam HALF_FFT_SIZE = FFT_SIZE / 2;

  always @* begin
    $display("Input: I=%0d, Q=%0d - Output: I=%0d, Q=%0d", i_tdata[31:16], i_tdata[15:0], o_tdata[31:16], o_tdata[15:0]);
  end


// Delay the input stream by FFT_SIZE
delay_fifo #(.WIDTH(32), .MAX_LEN(FFT_SIZE)) delay0(
    .clk(clk), .reset(reset), .clear(clear),
    .len(FFT_SIZE),
    .i_tdata(i_tdata), .i_tlast(i_tlast), .i_tvalid(i_tvalid), .i_tready(i_tready),
    .o_tdata(o_tdata), .o_tlast(o_tlast), .o_tvalid(o_tvalid), .o_tready(o_tready)
);

endmodule // my_module 