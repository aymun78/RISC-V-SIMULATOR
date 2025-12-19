module alu (
    input clk,
    input reset,
    input [31:0] A,
    input [31:0] B,
    input [3:0] ALUControl,
    output reg [31:0] Result,
    output Zero,
    output reg Busy
);

    /*
     ALU Control Lines:
     0000: AND
     0001: OR
     0010: ADD
     0011: XOR
     0100: SLL
     0101: SRL
     0110: SUB
     0111: SLT
     1000: MAX
     1001: GCD (Custom)
    */

    // FSM States
    localparam IDLE = 2'b00, CALC = 2'b01, DONE = 2'b10;
    reg [1:0] start_state, next_state; // Using start_state as current state register

    reg [31:0] a_reg, b_reg;
    reg [31:0] gcd_result;

    // FSM Sequential Logic
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            start_state <= IDLE;
            a_reg <= 0;
            b_reg <= 0;
            gcd_result <= 0;
        end else begin
            start_state <= next_state;
            if (start_state == IDLE && ALUControl == 4'b1001) begin
                a_reg <= A;
                b_reg <= B;
            end else if (start_state == CALC) begin
                if (a_reg > b_reg) a_reg <= a_reg - b_reg;
                else if (b_reg > a_reg) b_reg <= b_reg - a_reg;
            end
        end
    end

    // FSM Combinational Logic
    always @(*) begin
        next_state = start_state;
        Busy = 0;
        
        case(start_state)
            IDLE: begin
                if (ALUControl == 4'b1001) begin
                    next_state = CALC;
                    Busy = 1; // Busy immediately
                end
            end
            CALC: begin
                Busy = 1;
                if (a_reg == b_reg || a_reg == 0 || b_reg == 0) begin
                    next_state = DONE;
                    Busy = 1; // Still busy until we output in DONE (or we can drop it now if we are ready)
                    // Let's keep Busy high slightly to ensure stability or drop it.
                    // Requirement: "DONE: Lower the BUSY signal and output the result A."
                    // So in DONE state, Busy is low.
                    // But in CALC state, Busy is high.
                end
            end
            DONE: begin
                Busy = 0; // Operation Complete
                next_state = IDLE; // Auto return to IDLE
            end
        endcase
    end

    // Result Mux
    always @(*) begin
        case (ALUControl)
            4'b0000: Result = A & B;
            4'b0001: Result = A | B;
            4'b0010: Result = A + B;
            4'b0011: Result = A ^ B;
            4'b0100: Result = A << B[4:0];
            4'b0101: Result = A >> B[4:0];
            4'b0110: Result = A - B;
            4'b0111: Result = (A < B) ? 32'd1 : 32'd0;
            4'b1000: Result = (A > B) ? A : B;
            4'b1001: Result = (start_state == DONE) ? a_reg : 32'd0; // output GCD result when done
            default: Result = 32'd0;
        endcase
    end

    assign Zero = (Result == 0);

endmodule
