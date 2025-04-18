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

module metric_calculator #(
    parameter int FFT_SIZE = 1024,
    parameter int CP_SIZE = 128
)(
    input clk, 
    input reset,
    input clear,

    // Input signal for metric computation
    input [31:0] i_tdata,
    input i_tlast,
    input i_tvalid,
    output i_tready, 

    // M(d) schmidl-cox metric output
    output [32+$clog2(CP_SIZE+1)-1:0] m_tdata,
    output m_tlast,
    output m_tvalid,
    input m_tready,

    // Synchronised output signal
    output [31:0] o_tdata,
    output o_tlast,
    output o_tvalid,
    input o_tready
);

localparam CP_SIZE_WIDTH = $clog2(CP_SIZE + 1);

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


// Computationnal - compute the P(d) and R(d) metrics
wire [31:0] yl_tdata, p_tdata;          // 10 cycles latency
wire yl_tlast, yl_tvalid, yl_tready;
wire p_tlast, p_tvalid, p_tready;
symbol_autocorrelator #(
    .FFT_SIZE(FFT_SIZE)
) autocorrelator (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(i_cpy0_tdata),
    .i_tlast(i_cpy0_tlast),
    .i_tvalid(i_cpy0_tvalid),
    .i_tready(i_cpy0_tready),

    .o_tdata(yl_tdata),
    .o_tlast(yl_tlast),
    .o_tvalid(yl_tvalid),
    .o_tready(yl_tready),

    .p_tdata(p_tdata),
    .p_tlast(p_tlast),
    .p_tvalid(p_tvalid),
    .p_tready(p_tready)
);


wire [15:0] r_tdata;                    // 5 cycles latency
wire r_tlast, r_tvalid, r_tready;
symbol_energy #(
    .FFT_SIZE(FFT_SIZE)
) energy (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(i_cpy1_tdata),
    .i_tlast(i_cpy1_tlast),
    .i_tvalid(i_cpy1_tvalid),
    .i_tready(i_cpy1_tready),

    .o_tdata(r_tdata),
    .o_tlast(r_tlast),
    .o_tvalid(r_tvalid),
    .o_tready(r_tready)
);


// Compute |P(d)|^2
wire [31:0] abs2_p_tdata;               // 4 cycles latency
wire abs2_p_tlast, abs2_p_tvalid, abs2_p_tready;
complex_to_magsq #(
    .WIDTH(16)
) p_squared (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(p_tdata),
    .i_tlast(p_tlast),
    .i_tvalid(p_tvalid),
    .i_tready(p_tready),

    .o_tdata(abs2_p_tdata),
    .o_tlast(abs2_p_tlast),
    .o_tvalid(abs2_p_tvalid),
    .o_tready(abs2_p_tready)
);


// Compute |R(d)|^2
wire [15:0] r_cpy0_tdata, r_cpy1_tdata; // 1 cycle latency
wire r_cpy0_tlast, r_cpy1_tlast;
wire r_cpy0_tvalid, r_cpy1_tvalid;
wire r_cpy0_tready, r_cpy1_tready;
split_stream_fifo #(
    .WIDTH(16),
    .ACTIVE_MASK(4'b0011)
) r_splitter (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata(r_tdata),
    .i_tlast(r_tlast),
    .i_tvalid(r_tvalid),
    .i_tready(r_tready),

    .o0_tdata(r_cpy0_tdata),
    .o0_tlast(r_cpy0_tlast),
    .o0_tvalid(r_cpy0_tvalid),  
    .o0_tready(r_cpy0_tready),

    .o1_tdata(r_cpy1_tdata),
    .o1_tlast(r_cpy1_tlast),
    .o1_tvalid(r_cpy1_tvalid),
    .o1_tready(r_cpy1_tready),

    .o2_tready(1'b0),
    .o3_tready(1'b0)
);

wire [31:0] abs2_r_tdata;               // 3 cycles latency
wire abs2_r_tlast, abs2_r_tvalid, abs2_r_tready;
mult #(
    .WIDTH_A(16),
    .WIDTH_B(16),
    .WIDTH_P(32),
    .LATENCY(3)
) r_squared (
    .clk(clk),
    .reset(reset),

    .a_tdata(r_cpy0_tdata),
    .a_tlast(r_cpy0_tlast),
    .a_tvalid(r_cpy0_tvalid),
    .a_tready(r_cpy0_tready),

    .b_tdata(r_cpy1_tdata),
    .b_tlast(r_cpy1_tlast),
    .b_tvalid(r_cpy1_tvalid),
    .b_tready(r_cpy1_tready),

    .p_tdata(abs2_r_tdata),
    .p_tlast(abs2_r_tlast),
    .p_tvalid(abs2_r_tvalid),
    .p_tready(abs2_r_tready)
);

// Add latency to abs2_r_tdata to match the latency of abs2_p_tdata
wire [31:0] abs2_r_lat_tdata;
wire abs2_r_lat_tlast, abs2_r_lat_tvalid, abs2_r_lat_tready;
axi_latency #(
    .WIDTH(32),
    .DELAY(5) // (abs2_p - abs2_r) = (10 + 4) - (5 + 3 + 1) =  5
) delay_latency (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    
    .s_axis_tdata(abs2_r_tdata),
    .s_axis_tlast(abs2_r_tlast),
    .s_axis_tvalid(abs2_r_tvalid),
    .s_axis_tready(abs2_r_tready),
    
    .m_axis_tdata(abs2_r_lat_tdata),
    .m_axis_tlast(abs2_r_lat_tlast),
    .m_axis_tvalid(abs2_r_lat_tvalid),
    .m_axis_tready(abs2_r_lat_tready)
);


// Compute M(d) = |P(d)|^2 / (R(d))^2
wire [31:0] abs2_p_buf_tdata;               // 1 cycle latency
wire abs2_p_buf_tlast, abs2_p_buf_tvalid, abs2_p_buf_tready;
axi_fifo_short #(
    .WIDTH(33)
) abs2_p_buf (
    .clk(clk),
    .reset(reset),
    .clear(clear),

    .i_tdata({abs2_p_tdata << 12, abs2_p_tlast}), //! BUG SOURCE shift left because we have an integer division later
    .i_tvalid(abs2_p_tvalid),
    .i_tready(abs2_p_tready),

    .o_tdata({abs2_p_buf_tdata, abs2_p_buf_tlast}),
    .o_tvalid(abs2_p_buf_tvalid),
    .o_tready(abs2_p_buf_tready)
);

wire [31:0] abs2_r_lat_safebuf_tdata;               // 1 cycle latency
wire abs2_r_lat_safebuf_tlast, abs2_r_lat_safebuf_tvalid, abs2_r_lat_safebuf_tready;
safe_divisor #(
    .WIDTH(32)
) divisor_guard (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    
    .i_tdata(abs2_r_lat_tdata),
    .i_tlast(abs2_r_lat_tlast),
    .i_tvalid(abs2_r_lat_tvalid),
    .i_tready(abs2_r_lat_tready),
    
    .o_tdata(abs2_r_lat_safebuf_tdata),
    .o_tlast(abs2_r_lat_safebuf_tlast),
    .o_tvalid(abs2_r_lat_safebuf_tvalid),
    .o_tready(abs2_r_lat_safebuf_tready)
);


wire [31:0] metric_quotient_tdata, metric_rest_tdata;   // 71 cycles latency
wire metric_quotient_tlast, metric_quotient_tvalid, metric_quotient_tready;
divide_int32 divider (
    .aclk(clk),
    .aresetn(~reset),

    .s_axis_dividend_tdata(abs2_p_buf_tdata),
    .s_axis_dividend_tlast(abs2_p_buf_tlast),
    .s_axis_dividend_tvalid(abs2_p_buf_tvalid),
    .s_axis_dividend_tready(abs2_p_buf_tready),
    
    .s_axis_divisor_tdata(abs2_r_lat_safebuf_tdata),
    .s_axis_divisor_tlast(abs2_r_lat_safebuf_tlast),
    .s_axis_divisor_tvalid(abs2_r_lat_safebuf_tvalid),
    .s_axis_divisor_tready(abs2_r_lat_safebuf_tready),

    .m_axis_dout_tdata({metric_quotient_tdata, metric_rest_tdata}),
    .m_axis_dout_tlast(metric_quotient_tlast),
    .m_axis_dout_tvalid(metric_quotient_tvalid),
    .m_axis_dout_tready(metric_quotient_tready),
    .m_axis_dout_tuser()
);


// Moving sum - average the metric over a window of size CP
moving_sum #(                       // 1 cycle latency
    .WIDTH(32),
    .MAX_LEN(CP_SIZE)
) metric_sum (
    .clk(clk), 
    .reset(reset),
    .clear(clear),
    .len(CP_SIZE[CP_SIZE_WIDTH-1:0]),
    
    .i_tdata(metric_quotient_tdata),
    .i_tlast(metric_quotient_tlast),
    .i_tvalid(metric_quotient_tvalid),
    .i_tready(metric_quotient_tready),

    .o_tdata(m_tdata),
    .o_tlast(m_tlast),
    .o_tvalid(m_tvalid),
    .o_tready(m_tready)
);


// Add latency to the yl stream to match the latency of the metric
axi_latency #(
    .WIDTH(32),
    .DELAY(77) // metric - yl = (autocorr + abs + buf + div + ms) - yl = (10 + 4 + 1 + 71 + 1) - 10 =  77
) yl_latency (
    .clk(clk),
    .reset(reset),
    .clear(clear),
    
    .s_axis_tdata(yl_tdata),
    .s_axis_tlast(yl_tlast),
    .s_axis_tvalid(yl_tvalid),
    .s_axis_tready(yl_tready),
    
    .m_axis_tdata(o_tdata),
    .m_axis_tlast(o_tlast),
    .m_axis_tvalid(o_tvalid),
    .m_axis_tready(o_tready)
);

endmodule // metric_calculator