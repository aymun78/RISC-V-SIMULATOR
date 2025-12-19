module control_unit (
    input [6:0] Op,
    input [2:0] Funct3,
    input [6:0] Funct7,
    output reg RegWrite,
    output reg ALUSrc,
    output reg MemWrite,
    output reg [1:0] ResultSrc, // 00: ALU, 01: Mem, 10: PC+4
    output reg Branch,
    output reg Jump,
    output reg [3:0] ALUControl,
    output reg [1:0] ImmSrc // 00: I-type, 01: S-type, 10: B-type, 11: J-type
);

    reg [1:0] ALUOp;

    always @(*) begin
        // Defaults
        RegWrite = 0; ALUSrc = 0; MemWrite = 0; ResultSrc = 0; 
        Branch = 0; Jump = 0; ALUOp = 0; ImmSrc = 0;

        case(Op)
            7'b0110011: begin // R-type
                RegWrite = 1;
                ALUOp = 2'b10;
            end
            7'b0010011: begin // I-type ALU (ADDI)
                RegWrite = 1;
                ALUSrc = 1;
                ALUOp = 2'b10; // Treat like R-type calculation (ADD) but with Immediate
                ImmSrc = 2'b00;
            end
            7'b0000011: begin // LW
                RegWrite = 1;
                ALUSrc = 1;
                ResultSrc = 2'b01;
                ImmSrc = 2'b00;
                ALUOp = 2'b00; // ADD for addr calc
            end
            7'b0100011: begin // SW
                MemWrite = 1;
                ALUSrc = 1;
                ImmSrc = 2'b01;
                ALUOp = 2'b00; // ADD for addr calc
            end
            7'b1100011: begin // BEQ
                Branch = 1;
                ALUOp = 2'b01; // Subtract for comparison
                ImmSrc = 2'b10;
            end
            7'b1101111: begin // JAL
                Jump = 1;
                RegWrite = 1;
                ResultSrc = 2'b10;
                ImmSrc = 2'b11;
            end
            7'b0001011: begin // GCD (Custom)
                RegWrite = 1;
                ALUOp = 2'b10; // Use R-type encoding for Funct3/7 check or just force straight to ALUControl logic
                 // If the user wants to use Funct3 to differentiate, we can. 
                 // But the prompt says "Opcode: 7'b0001011" implicitly defining the instruction.
                 // It doesn't specify R-type or I-type format explicitly but "GCD rd, rs1, rs2" implies R-type register args.
                 // Let's assume R-type format (Op=0001011, rd, rs1, rs2, funct3=?, funct7=?)
                 // or maybe just Opcode is enough.
                 // Let's set ALUOp to a special value or just handle it in the next block.
                 // Since ALUControl logic depends on ALUOp, let's leave it as 2'b10 (R-type like) 
                 // and handle the Opcode in the ALU Decoder below.
            end
        endcase
    end

    // ALU Decoder
    always @(*) begin
        case(ALUOp)
            2'b00: ALUControl = 4'b0010; // ADD (LW/SW)
            2'b01: ALUControl = 4'b0110; // SUB (BEQ)
            2'b10: begin // R-type and I-type (ADDI/SLLI/SRLI)
                if (Op == 7'b0010011) begin 
                     case(Funct3)
                        3'b000: ALUControl = 4'b0010; // ADDI
                        3'b001: ALUControl = 4'b0100; // SLLI
                        3'b101: ALUControl = 4'b0101; // SRLI
                        default: ALUControl = 4'b0010; 
                     endcase
                end else if (Op == 7'b0001011) begin
                    // GCD Instruction
                    ALUControl = 4'b1001;
                end else begin      
                    // R-Type
                    case(Funct3)
                        3'b000: begin
                            if (Funct7[5]) ALUControl = 4'b0110; // SUB
                            else ALUControl = 4'b0010;          // ADD
                        end
                        3'b001: ALUControl = 4'b0100; // SLL
                        3'b010: ALUControl = 4'b0111; // SLT
                        3'b011: ALUControl = 4'b1000; // MAX (Custom, Funct3=011)
                        3'b100: ALUControl = 4'b0011; // XOR (Standard RISC-V 100)
                        3'b101: ALUControl = 4'b0101; // SRL
                        3'b110: ALUControl = 4'b0001; // OR
                        3'b111: ALUControl = 4'b0000; // AND
                        default: ALUControl = 4'b0000;
                    endcase
                end
            end
            default: ALUControl = 4'b0000;
        endcase
    end

endmodule
