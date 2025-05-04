module detector #(
  parameter int HALF_FFT_SIZE = 512,
  parameter int HALPH_CP_SIZE = 64,
  parameter int M_TDATA_WIDTH = 32
) 
(
  input clk,
  input reset, 
  input clear,

  // Configuration inputs
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
  input o_tready,

  // Signaling ouputs
  output end_of_ofdm_packet,
  output [15:0] rfnoc_packet_length
);

// Number of samples after the peak to be at CP/2 of the 1st OFDM symbol
localparam int MAX_COUNT = HALF_FFT_SIZE + HALPH_CP_SIZE; 

logic fsm_ready;
logic is_last_forwarded_sample;

// States
logic[31:0] max_val;
logic[31:0] max_val_counter;
logic[31:0] nbr_forwarded_samples;
logic[15:0] rfnoc_packet_length_val;
logic[15:0] rfnoc_packet_length_allframe_val;
logic[31:0] searching_idx;
logic[31:0] detected_idx;
logic[31:0] maximum_idx;
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
    fsm_ready <= 0;
    is_last_forwarded_sample <= 0;

    current_state <= SEARCHING;
    max_val <= 0;
    max_val_counter <= MAX_COUNT;
    nbr_forwarded_samples <= 0;
    is_valid <= 0;
    rfnoc_packet_length_val <= 16'd1;
    
    rfnoc_packet_length_allframe_val <= 16'd1;
    searching_idx <= 0;
    detected_idx <= 0;
    maximum_idx <= 0;
    
  end

  // State transitions
  else begin
    // Default values
    fsm_ready <= 1;
    is_last_forwarded_sample <= 0;

    // Keep the current state and values by default
    current_state <= current_state;
    max_val <= max_val;
    max_val_counter <= max_val_counter;
    nbr_forwarded_samples <= nbr_forwarded_samples;
    is_valid <= is_valid;
    rfnoc_packet_length_val <= rfnoc_packet_length_val;

    // Idx computation
    if (i_tvalid) begin
      if (i_tlast) begin
        rfnoc_packet_length_allframe_val <= 16'd1;
      end else begin
        rfnoc_packet_length_allframe_val <= rfnoc_packet_length_allframe_val + 1;
      end
    end else begin
      rfnoc_packet_length_allframe_val <= rfnoc_packet_length_allframe_val;
    end
    searching_idx <= searching_idx;
    detected_idx <= detected_idx;
    maximum_idx <= maximum_idx;

    case (current_state)
      // SEARCHING state: waiting for metric to exceed threshold
      SEARCHING: begin
        if (m_tvalid) begin
          // Metric is high enough => start detecting
          if (m_tdata > threshold) begin
            current_state <= DETECTING;
            max_val <= m_tdata;
            max_val_counter <= MAX_COUNT - 1;
            detected_idx <= 2; // ! Fix because it needs 1 cyle for the maximum idx
          end 
          
          // In searching state
          else begin 
            searching_idx <= searching_idx + 1;
          end
        end
      end


      // DETECTING state: find the maximum value
      DETECTING: begin
        if (m_tvalid) begin
          if (m_tdata > threshold) begin
            if (m_tdata >= max_val) begin // Check for new maximum value
              max_val <= m_tdata;
              max_val_counter <= MAX_COUNT - 1;
              maximum_idx <= searching_idx + detected_idx;
            end else begin
              max_val_counter <= max_val_counter - 1;
            end
            detected_idx <= detected_idx + 1;
          end

          // Metric is too small => detected state
          else begin
            current_state <= DETECTED;
            max_val_counter <= max_val_counter - 1;
          end
        end
      end


      // DETECTED state: wait for the counter to reach 0
      DETECTED: begin
        if (m_tvalid) begin
          if (max_val_counter > 0) begin
            max_val_counter <= max_val_counter - 1;
          end 
          
          // Counter reached 0 => start forwarding (current sample is valid !)
          else begin
            current_state <= FORWARDING;
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= 1;
            is_valid <= 1;
            rfnoc_packet_length_val <= 16'd1;
          end
        end
      end

      // FORWARDING state: forward samples until packet_length is reached
      FORWARDING: begin
        if (m_tvalid) begin
          if (nbr_forwarded_samples < packet_length) begin
            // Check for last sample
            if (nbr_forwarded_samples + 1 == packet_length) begin
              is_last_forwarded_sample <= 1;
            end
            // Update packet lenght
            if (i_tlast) begin
              rfnoc_packet_length_val <= 16'd1;
            end else begin
              rfnoc_packet_length_val <= rfnoc_packet_length_val + 1;
            end
            nbr_forwarded_samples <= nbr_forwarded_samples + 1;
          
          // Reset the state machine for the next packet
          end else begin
            current_state <= SEARCHING;
            max_val <= 0;
            max_val_counter <= MAX_COUNT;
            nbr_forwarded_samples <= 0;
            is_valid <= 0;
            rfnoc_packet_length_val <= 16'd1;

            rfnoc_packet_length_allframe_val <= 16'd1;
            searching_idx <= 0;
            detected_idx <= 0;
            maximum_idx <= 0;
          end
        end
      end

      default: begin
        current_state <= SEARCHING;
        max_val <= 0;
        max_val_counter <= MAX_COUNT;
        nbr_forwarded_samples <= 0;
        is_valid <= 0;
        rfnoc_packet_length_val <= 16'd1;
        searching_idx <= 0;
        detected_idx <= 0;
        maximum_idx <= 0;
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
      selected_o_tlast = is_valid ? (i_tlast || is_last_forwarded_sample): is_last_forwarded_sample;
    end
    2'b10: begin // Test sequence: forward the entire frame, last sample is replaced by the maximum_idx
      selected_o_tdata = is_last_forwarded_sample ? maximum_idx : i_tdata;
      selected_o_tvalid = i_tvalid;
      selected_o_tlast = i_tlast || is_last_forwarded_sample;
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
assign end_of_ofdm_packet = is_last_forwarded_sample;
assign rfnoc_packet_length = output_select == 2'b10 ? rfnoc_packet_length_allframe_val : rfnoc_packet_length_val;

endmodule // detector
