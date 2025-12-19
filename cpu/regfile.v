module regfile (
    input clk,
    input we3,           // Write Enable
    input [4:0] ra1,     // Read Address 1
    input [4:0] ra2,     // Read Address 2
    input [4:0] wa3,     // Write Address 3
    input [31:0] wd3,    // Write Data 3
    output [31:0] rd1,   // Read Data 1
    output [31:0] rd2    // Read Data 2
);

    reg [31:0] rf [31:0];

    // Initialize registers to 0 (useful for simulation)
    integer i;
    initial begin
        for (i = 0; i < 32; i = i + 1)
            rf[i] = 32'd0;
    end

    // x0 is always 0.
    // Combinatorial Read
    // Combinatorial Read with Write-Through Forwarding
    assign rd1 = (ra1 != 0) ? ((ra1 == wa3 && we3) ? wd3 : rf[ra1]) : 32'd0;
    assign rd2 = (ra2 != 0) ? ((ra2 == wa3 && we3) ? wd3 : rf[ra2]) : 32'd0;

    // Synchronous Write
    always @(posedge clk) begin
        if (we3 && wa3 != 0) begin
            rf[wa3] <= wd3;
        end
    end

endmodule
