module datapath(
    input clk, reset,
    output [31:0] PC_out,
    output [31:0] ALUResult_out,
    output [31:0] WriteData_out,
    output MemWrite_out
);
    // Internal Wires
    wire [31:0] PC, PCNext, PCPlus4, PCTarget;
    wire [31:0] Instr;
    wire [31:0] RD1, RD2, ImmExt;
    wire [31:0] SrcA, SrcB, ALUResult;
    wire [31:0] ReadData, Result;
    wire Zero;
    
    // Control Signals
    wire RegWrite, ALUSrc, MemWrite, Branch, Jump;
    wire [1:0] ResultSrc, ImmSrc;
    wire [3:0] ALUControl;
    
    // Pipeline Registers
    reg [31:0] IF_ID_PC, IF_ID_Instr;
    reg [31:0] ID_EX_PC, ID_EX_RD1, ID_EX_RD2, ID_EX_Imm;
    reg [4:0]  ID_EX_Rd, ID_EX_Rs1, ID_EX_Rs2;
    reg        ID_EX_RegWrite, ID_EX_MemWrite, ID_EX_ALUSrc, ID_EX_Branch, ID_EX_Jump;
    reg [1:0]  ID_EX_ResultSrc;
    reg [3:0]  ID_EX_ALUControl; // Passed for EX
    
    reg [31:0] EX_MEM_ALUResult, EX_MEM_WriteData;
    reg [4:0]  EX_MEM_Rd;
    reg        EX_MEM_RegWrite, EX_MEM_MemWrite;
    reg [1:0]  EX_MEM_ResultSrc;
    
    reg [31:0] MEM_WB_ReadData, MEM_WB_ALUResult;
    reg [4:0]  MEM_WB_Rd;
    reg        MEM_WB_RegWrite;
    reg [1:0]  MEM_WB_ResultSrc;

    // --- Hazard Detection Unit ---
    reg Stall;
    wire AluBusy;
    always @(*) begin
        Stall = 0;
        // Check if instruction in EX is a Load (ResultSrc 01 is Mem)
        if (ID_EX_ResultSrc == 2'b01) begin
            // Check if Load destination matches current ID source registers
            if ((ID_EX_Rd != 0) && ((ID_EX_Rd == IF_ID_Instr[19:15]) || (ID_EX_Rd == IF_ID_Instr[24:20]))) begin
                Stall = 1;
            end
        end
        if (AluBusy) Stall = 1;
    end

    // --- Fetch Stage ---
    reg [31:0] PC_reg;
    always @(posedge clk or posedge reset) begin
        if (reset) PC_reg <= 0;
        else if (!Stall) PC_reg <= PCNext; // Stall PC
    end
    
    assign PC = PC_reg;
    assign PCPlus4 = PC + 4;
    assign PC_out = PC; // Output for observation

    // Mux for PC Source (Branch/Jump)
    wire PCSrc; 
    
    instr_memory imem (.A(PC), .RD(Instr));

    // IF/ID Register
    always @(posedge clk) begin
        if (reset || PCSrc) begin
            IF_ID_PC <= 0;
            IF_ID_Instr <= 0;
        end else if (!Stall) begin // Stall IF/ID
            IF_ID_PC <= PC;
            IF_ID_Instr <= Instr;
        end
    end

    // --- Decode Stage ---
    control_unit cu (
        .Op(IF_ID_Instr[6:0]), 
        .Funct3(IF_ID_Instr[14:12]), 
        .Funct7(IF_ID_Instr[31:25]),
        .RegWrite(RegWrite), 
        .ALUSrc(ALUSrc), 
        .MemWrite(MemWrite), 
        .ResultSrc(ResultSrc), 
        .Branch(Branch), 
        .Jump(Jump), 
        .ALUControl(ALUControl), 
        .ImmSrc(ImmSrc)
    );

    regfile rf (
        .clk(clk), 
        .we3(MEM_WB_RegWrite), 
        .ra1(IF_ID_Instr[19:15]), 
        .ra2(IF_ID_Instr[24:20]), 
        .wa3(MEM_WB_Rd), 
        .wd3(Result), 
        .rd1(RD1), 
        .rd2(RD2)
    );

    imm_gen ig (
        .Instr(IF_ID_Instr[31:7]), 
        .ImmSrc(ImmSrc), 
        .ImmExt(ImmExt)
    );

    // ID/EX Register
    // Helper signal to distinguish Load-Use Stall from AluBusy Stall
    wire LoadUseStall;
    assign LoadUseStall = (ID_EX_ResultSrc == 2'b01) && ((ID_EX_Rd != 0) && ((ID_EX_Rd == IF_ID_Instr[19:15]) || (ID_EX_Rd == IF_ID_Instr[24:20])));

    always @(posedge clk) begin
        // Flush if Reset, Branch Taken, OR Load-Use Stall (Inject NOP bubble)
        if (reset || PCSrc || LoadUseStall) begin
            ID_EX_PC <= 0; ID_EX_RD1 <= 0; ID_EX_RD2 <= 0; ID_EX_Imm <= 0; ID_EX_Rd <= 0;
            ID_EX_Rs1 <= 0; ID_EX_Rs2 <= 0;
            ID_EX_RegWrite <= 0; ID_EX_MemWrite <= 0; ID_EX_ALUSrc <= 0; ID_EX_ResultSrc <= 0; ID_EX_ALUControl <= 0;
            ID_EX_Branch <= 0; ID_EX_Jump <= 0;
        end else if (!AluBusy) begin 
            // Update only if ALU is NOT busy. If ALU is busy, we freeze (retain values).
            ID_EX_PC <= IF_ID_PC;
            ID_EX_RD1 <= RD1;
            ID_EX_RD2 <= RD2;
            ID_EX_Imm <= ImmExt;
            ID_EX_Rd <= IF_ID_Instr[11:7];
            ID_EX_Rs1 <= IF_ID_Instr[19:15];
            ID_EX_Rs2 <= IF_ID_Instr[24:20];
            ID_EX_RegWrite <= RegWrite;
            ID_EX_MemWrite <= MemWrite;
            ID_EX_ALUSrc <= ALUSrc;
            ID_EX_ResultSrc <= ResultSrc;
            ID_EX_ALUControl <= ALUControl;
            ID_EX_Branch <= Branch;
            ID_EX_Jump <= Jump;
        end
    end

    // --- Execute Stage ---
    
    // --- Execute Stage ---
    
    // Forwarding Logic
    reg [1:0] ForwardA, ForwardB;
    always @(*) begin
        ForwardA = 2'b00;
        ForwardB = 2'b00;
        
        // EX Hazard (Forward from MEM stage)
        if (EX_MEM_RegWrite && (EX_MEM_Rd != 0) && (EX_MEM_Rd == ID_EX_Rs1))
            ForwardA = 2'b10;
        else if (MEM_WB_RegWrite && (MEM_WB_Rd != 0) && (MEM_WB_Rd == ID_EX_Rs1))
            ForwardA = 2'b01; // MEM Hazard (Forward from WB stage)

        if (EX_MEM_RegWrite && (EX_MEM_Rd != 0) && (EX_MEM_Rd == ID_EX_Rs2))
            ForwardB = 2'b10;
        else if (MEM_WB_RegWrite && (MEM_WB_Rd != 0) && (MEM_WB_Rd == ID_EX_Rs2))
            ForwardB = 2'b01;
    end

    // ALU Source Muxes with Forwarding
    reg [31:0] SrcA_mux, SrcB_fwd;
    always @(*) begin
        // SrcA Mux
        case(ForwardA)
            2'b00: SrcA_mux = ID_EX_RD1;
            2'b10: SrcA_mux = EX_MEM_ALUResult;
            2'b01: SrcA_mux = Result; // Result is from WB stage (Writeback value)
            default: SrcA_mux = ID_EX_RD1;
        endcase

        // SrcB Forwarding Mux
        case(ForwardB)
            2'b00: SrcB_fwd = ID_EX_RD2;
            2'b10: SrcB_fwd = EX_MEM_ALUResult;
            2'b01: SrcB_fwd = Result;
            default: SrcB_fwd = ID_EX_RD2;
        endcase
    end
    
    assign SrcA = SrcA_mux;
    assign SrcB = (ID_EX_ALUSrc) ? ID_EX_Imm : SrcB_fwd;
    
    alu alu_inst (
        .clk(clk),
        .reset(reset),
        .A(SrcA), 
        .B(SrcB), 
        .ALUControl(ID_EX_ALUControl), 
        .Result(ALUResult), 
        .Zero(Zero),
        .Busy(AluBusy)
    );

    // EX/MEM Register
    always @(posedge clk) begin
        if (reset) begin
            EX_MEM_ALUResult <= 0; EX_MEM_WriteData <= 0; EX_MEM_Rd <= 0;
            EX_MEM_RegWrite <= 0; EX_MEM_MemWrite <= 0; EX_MEM_ResultSrc <= 0;
        end else if (!AluBusy) begin
            EX_MEM_ALUResult <= ALUResult;
            EX_MEM_WriteData <= SrcB_fwd; // Store Data comes from Forwarded RD2
            EX_MEM_Rd <= ID_EX_Rd;
            EX_MEM_RegWrite <= ID_EX_RegWrite;
            EX_MEM_MemWrite <= ID_EX_MemWrite;
            EX_MEM_ResultSrc <= ID_EX_ResultSrc;
        end else begin
            // Insert NOP (Bubble) into MEM stage while ALU is busy
            EX_MEM_RegWrite <= 0;
            EX_MEM_MemWrite <= 0;
            EX_MEM_ALUResult <= 0;
            EX_MEM_WriteData <= 0;
            EX_MEM_Rd <= 0;
            EX_MEM_ResultSrc <= 0;
        end
    end

    // --- Memory Stage ---
    data_memory dmem (
        .clk(clk), 
        .we(EX_MEM_MemWrite), 
        .A(EX_MEM_ALUResult), 
        .WD(EX_MEM_WriteData), 
        .RD(ReadData)
    );

    // MEM/WB Register
    always @(posedge clk) begin
        if (reset) begin
            MEM_WB_ReadData <= 0; MEM_WB_ALUResult <= 0; MEM_WB_Rd <= 0;
            MEM_WB_RegWrite <= 0; MEM_WB_ResultSrc <= 0;
        end else begin
            MEM_WB_ReadData <= ReadData;
            MEM_WB_ALUResult <= EX_MEM_ALUResult;
            MEM_WB_Rd <= EX_MEM_Rd;
            MEM_WB_RegWrite <= EX_MEM_RegWrite;
            MEM_WB_ResultSrc <= EX_MEM_ResultSrc;
        end
    end

    // --- Writeback Stage ---
    assign Result = (MEM_WB_ResultSrc == 2'b01) ? MEM_WB_ReadData : MEM_WB_ALUResult;

    // --- PC Logic (Simplified) ---
    // For this basic design, we will just count up. 
    // Implementing Branching in a pipelined CPU without flushing logic is tricky.
    // I will use a simple assumption: Branch taken updates PCNext.
    // And we assume software inserts NOPs to handle the delay slot if needed, or we just take the penalty.
    
    // NOTE: Real branching happens here. 
    // If Branch is taken (Zero & Branch signal from ID stage? No, must be EX stage).
    // Let's forward the Branch/Zero signal to EX stage or decide in ID.
    // For simplicity of this artifact: I'm making PCNext logic simple.
    
    assign PCTarget = ID_EX_PC + ID_EX_Imm;
    assign PCSrc = (ID_EX_Branch & Zero) | ID_EX_Jump;
    assign PCNext = (PCSrc) ? PCTarget : PCPlus4;
    // Full Branch support omitted for brevity in this specific file to ensure basic flow works first. 
    // (User can see instructions flowing through stages).

    assign ALUResult_out = EX_MEM_ALUResult;
    assign WriteData_out = EX_MEM_WriteData;
    assign MemWrite_out = EX_MEM_MemWrite;

endmodule
