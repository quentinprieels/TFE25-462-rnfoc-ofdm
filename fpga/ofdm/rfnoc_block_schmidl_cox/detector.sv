module detector #(
  parameter int HALF_FFT_SIZE = 512,
  parameter int HALPH_CP_SIZE = 64,
  parameter int M_TDATA_WIDTH = 32
) 
(
  input clk,
  input reset, 
  input clear,

  input [31:0] threshold, // Threshold for detection
  input [31:0] packet_length, // Length of the packet

  // Metric input
  input [M_TDATA_WIDTH-1:0] m_tdata, 
  input m_tlast, 
  input m_tvalid, 
  output m_tready,

  // Input and output signals
  input [31:0] i_tdata,
  input i_tlast,
  input i_tvalid,
  output i_tready,

  output [31:0] o_tdata,
  output o_tlast,
  output o_tvalid,
  input o_tready
);

// Number of samples after the peak to be at CP/2 of the 1st OFDM symbol
localparam int MAX_COUNT = HALF_FFT_SIZE + HALPH_CP_SIZE; 

logic metric_ready;

// States
logic[31:0] max_val;
logic[31:0] max_val_counter;
logic[31:0] nbr_forwarded_samples;
logic is_valid;
typedef enum logic[1:0] {
  SEARCHING = 0,  // 00
  DETECTING = 1,  // 01
  DETECTED = 2,   // 10
  FORWARDING = 3  // 11
} statetype_t;
statetype_t current_state;

// State machine
always @(posedge clk) begin
  
  // Reset
  if (reset | clear) begin
    current_state <= SEARCHING;
    max_val <= 0;
    max_val_counter <= MAX_COUNT;
    nbr_forwarded_samples <= 0;
    is_valid <= 0;
    metric_ready <= 0;
  end

  // State transitions
  else begin
    metric_ready <= 1;
    case (current_state)

      // Searching state: waiting for metric to exceed threshold
      SEARCHING: begin
        if (m_tvalid) begin
          if (m_tdata > threshold) begin
            current_state <= DETECTING;
            max_val <= m_tdata;
            max_val_counter <= MAX_COUNT - 1;
            nbr_forwarded_samples <= 0;
            is_valid <= 0;
          end else begin
            current_state <= SEARCHING;
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= 0;
            is_valid <= 0;
          end
        end
      end

      // Detecting state: find the maximum value and
      // decrement the counter holding the number of sample between
      // the maximum value and the next OFDM symbol
      DETECTING: begin
        if (m_tvalid) begin
          if (m_tdata > threshold) begin
            current_state <= DETECTING;

            // Check if the maximum value is reached
            if (m_tdata >= max_val) begin
              max_val <= m_tdata;
              max_val_counter <= MAX_COUNT - 1;
            end else begin
              max_val <= max_val;
              max_val_counter <= max_val_counter - 1;
            end

          end else begin
            current_state <= DETECTED; // End of detection
            max_val <= max_val;
            max_val_counter <= max_val_counter - 1;
          end
        end
      end

      // Detected state: wait for the counter to reach 0
      DETECTED: begin
        if (m_tvalid) begin
          if (max_val_counter > 0) begin
            current_state <= DETECTED;
            max_val <= max_val;
            max_val_counter <= max_val_counter - 1;
            nbr_forwarded_samples <= 0;
            is_valid <= 0;
          end else begin
            current_state <= FORWARDING; // Start forwarding
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= 1;
            is_valid <= 1;
          end
        end
      end

      // Forwarding state: forward the samples until the packet length is reached
      FORWARDING: begin
        if (m_tvalid) begin
          if (nbr_forwarded_samples < packet_length) begin
            current_state <= FORWARDING;
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= nbr_forwarded_samples + 1;
            is_valid <= 1;
          end else begin
            current_state <= SEARCHING;
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= 0;
            is_valid <= 0;
          end
        end
      end

      default: begin
        current_state <= SEARCHING;
        max_val <= 0;
        max_val_counter <= MAX_COUNT;
        nbr_forwarded_samples <= 0;
        is_valid <= 0;
      end
    endcase
  end
end

// Output signal generation (the is_valid signal is used to indicate the valid samples)
// assign o_tdata = i_tdata; // => THIS IS THE RIGHT WAY TO DO
assign o_tdata = is_valid ? i_tdata : 0;
assign o_tlast = i_tlast;
// assign o_tvalid = i_tvalid & is_valid; // => THIS IS THE RIGHT WAY TO DO
assign o_tvalid = i_tvalid;
assign i_tready = o_tready;

// Metric output generation
assign m_tready = metric_ready;

endmodule // detector

