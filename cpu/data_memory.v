module data_memory (
    input clk,
    input we,
    input [31:0] A,
    input [31:0] WD,
    output [31:0] RD
);

    reg [31:0] ram [255:0]; // 256 words Data Memory

    // Initialize to 0 then load program
    integer i;
    initial begin
        for (i = 0; i < 256; i = i + 1)
            ram[i] = 32'd0;
        $readmemh("program.hex", ram);
    end

    assign RD = ram[A[31:2]]; // Word aligned

    always @(posedge clk) begin
        if (we) begin
            ram[A[31:2]] <= WD;
        end
    end

endmodule
