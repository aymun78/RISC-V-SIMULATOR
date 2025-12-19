module instr_memory (
    input [31:0] A,
    output [31:0] RD
);

    reg [31:0] ram [0:1023]; // 1024 words (4KB instructions approx)

    integer i;
    initial begin
        // Initialize to 0 (NOPs)
        for (i = 0; i < 1024; i = i + 1)
            ram[i] = 32'd0;
            
        // Load program from file
        $readmemh("program.hex", ram);
    end

    // Word Aligned Read
    assign RD = ram[A[31:2]]; 

endmodule
