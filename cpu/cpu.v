module cpu(
    input clk,
    input reset,
    output [31:0] PC,
    output [31:0] ALUResult,
    output [31:0] MemWriteData,
    output MemWrite
);

    datapath dp(
        .clk(clk),
        .reset(reset),
        .PC_out(PC),
        .ALUResult_out(ALUResult),
        .WriteData_out(MemWriteData),
        .MemWrite_out(MemWrite)
    );

endmodule
