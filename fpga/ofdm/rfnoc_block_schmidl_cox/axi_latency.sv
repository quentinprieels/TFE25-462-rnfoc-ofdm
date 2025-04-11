//
// AXI Shift Register Module
//
// This module implements a shift register for AXI Stream data.
// It allows for a configurable delay in the data stream.
// The module delay all input signals by a specified number of clock cycles.
// The delay is implemented using a series of registers.
// The module also includes a clear signal to reset the registers.
//

module axi_latency #(
    parameter WIDTH = 32,
    parameter DELAY = 8
) (
    input clk,
    input reset,
    input clear,
    
    // Input AXI Stream
    input [WIDTH-1:0] s_axis_tdata,
    input s_axis_tlast,
    input s_axis_tvalid,
    output s_axis_tready,
    
    // Output AXI Stream 
    output [WIDTH-1:0] m_axis_tdata,
    output m_axis_tlast,
    output m_axis_tvalid,
    input m_axis_tready
);

    // Registers for data and control signals
    reg [WIDTH-1:0] data_regs [0:DELAY-1];
    reg last_regs [0:DELAY-1];
    reg valid_regs [0:DELAY-1];
    
    // Ready signal affects all stages
    wire ready_all = m_axis_tready || !valid_regs[DELAY-1];
    assign s_axis_tready = ready_all;
    
    always @(posedge clk) begin
        if (reset || clear) begin
            for (int i = 0; i < DELAY; i++) begin
                valid_regs[i] <= 1'b0;
                last_regs[i] <= 1'b0;
                data_regs[i] <= {WIDTH{1'b0}};
            end
        end else if (ready_all) begin
            // Shift everything when ready
            for (int i = DELAY-1; i > 0; i--) begin
                valid_regs[i] <= valid_regs[i-1];
                last_regs[i] <= last_regs[i-1];
                data_regs[i] <= data_regs[i-1];
            end
            // Input stage
            valid_regs[0] <= s_axis_tvalid;
            last_regs[0] <= s_axis_tlast;
            data_regs[0] <= s_axis_tdata;
        end
    end
    
    // Assign outputs
    assign m_axis_tvalid = valid_regs[DELAY-1];
    assign m_axis_tlast = last_regs[DELAY-1];
    assign m_axis_tdata = data_regs[DELAY-1];

endmodule // axi_latency