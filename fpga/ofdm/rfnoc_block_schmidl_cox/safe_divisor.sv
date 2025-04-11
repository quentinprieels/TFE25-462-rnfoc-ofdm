module safe_divisor #(
    parameter WIDTH = 32
) (
    input clk,
    input reset,
    input clear,

    // Input signals
    input [WIDTH-1:0] i_tdata,
    input i_tlast,
    input i_tvalid,
    output i_tready,

    // Output signals
    output reg [WIDTH-1:0] o_tdata,
    output reg o_tlast,
    output reg o_tvalid,
    input o_tready
);

reg ready_int;
assign i_tready = ready_int;

always @(posedge clk) begin
    if (reset || clear) begin
        o_tdata <= {WIDTH{1'b1}};
        o_tlast <= 1'b0;
        o_tvalid <= 1'b0;
        ready_int <= 1'b1;
    end else begin 
        if (ready_int && i_tvalid) begin
            // Capture the input data
            o_tdata <= (i_tdata == 0) ? {{(WIDTH-1){1'b0}}, 1'b1} : i_tdata;
            o_tlast <= i_tlast;
            o_tvalid <= 1'b1;
            ready_int <= o_tready; // Only ready if output is ready
        end else if (o_tready) begin
            // Output has been accepted, we can accept new data
            o_tvalid <= 1'b0;
            ready_int <= 1'b1;
        end
    end
end

endmodule // safe_divisor