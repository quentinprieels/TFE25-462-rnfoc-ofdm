module detector #(
  parameter int HALF_FFT_SIZE = 512,
  parameter int HALPH_CP_SIZE = 64,
  parameter int M_TDATA_WIDTH = 32
) 
(
  input clk,
  input reset, 
  input clear,

  input [31:0] threshold,     // Threshold for detection
  input [31:0] packet_length, // Length of the packet
  input [1:0]  output_select, // Output select signal (00: signal, 10: metric MSB, 11: metric LSB)

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

logic fsm_ready;
logic is_last_forwarded_sample;

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
    fsm_ready <= 0;
    is_last_forwarded_sample <= 0;
  end

  // State transitions
  else begin
    fsm_ready <= 1;
    is_last_forwarded_sample <= 0; // By default, not the last sample

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
            if (nbr_forwarded_samples + 1 == packet_length) begin
              is_last_forwarded_sample <= 1; // Last sample to be forwarded
            end 
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
        is_last_forwarded_sample <= 0;
      end
    endcase
  end
end

// New output logic
logic [31:0] selected_o_tdata;
logic selected_o_tvalid;
logic selected_o_tlast;

always_comb begin
  // Default values
  selected_o_tdata = 32'b0;
  selected_o_tvalid = 0;
  selected_o_tlast = 0;

  case (output_select)
    2'b00: begin // i_tdata when valid, else 0 => same packet properties as i
      selected_o_tdata = is_valid ? i_tdata : 32'b0;
      selected_o_tvalid = i_tvalid;
      selected_o_tlast = i_tlast;
    end
    2'b01: begin // i_tdata, only when valid
      selected_o_tdata = i_tdata;
      selected_o_tvalid = i_tvalid & is_valid;
      selected_o_tlast = is_valid ? i_tlast || is_last_forwarded_sample: is_last_forwarded_sample;
    end
    2'b10: begin // metric MSB
      selected_o_tdata = m_tdata[M_TDATA_WIDTH-1 -: 32];
      selected_o_tvalid = m_tvalid;
      selected_o_tlast = m_tlast;
    end
    2'b11: begin // metric LSB
      selected_o_tdata = m_tdata[31:0];
      selected_o_tvalid = m_tvalid;
      selected_o_tlast = m_tlast;
    end
    default: begin
      selected_o_tdata = 32'b0;
      selected_o_tvalid = 0;
      selected_o_tlast = 0;
    end
  endcase
end

assign o_tdata = selected_o_tdata;
assign o_tvalid = selected_o_tvalid;
assign o_tlast = selected_o_tlast;
assign i_tready = o_tready & fsm_ready;
assign m_tready = o_tready & fsm_ready;


endmodule // detector
