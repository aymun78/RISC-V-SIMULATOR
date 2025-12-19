`timescale 1ns / 1ps

module cpu_tb;

    reg clk;
    reg reset;
    
    // CPU Interfaces? If CPU has no outputs, we just spy on internal signals
    // Assuming 'cpu' module exists
    wire [31:0] PC;
    wire [31:0] ALUResult;
    wire [31:0] MemWriteData;
    wire MemWrite;

    cpu uut (
        .clk(clk),
        .reset(reset),
        .PC(PC),
        .ALUResult(ALUResult),
        .MemWriteData(MemWriteData),
        .MemWrite(MemWrite)
    );

    // Clock Generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period
    end

    // Test Sequence
    initial begin
        // Dump logic for waveform viewing
        $dumpfile("cpu_wave.vcd");
        $dumpvars(0, cpu_tb);

        reset = 1;
        #20;
        reset = 0;
        
        #1000; // Run for some time
        $finish;
    end
    
    // Monitor key signals (Adjust paths based on your hierarchy)
    // Example: $display PC every cycle
    // Monitor execution
    always @(posedge clk) begin
        if (!reset) begin
            // Display PC and Instruction to verify what is executing
            $display("Time: %t | PC: %h | Instr: %h", $time, uut.dp.PC, uut.dp.Instr);
            
            // Monitor Register Writes (simplified check)
            if (uut.dp.rf.we3) begin
                 $display("  -> Write Reg x%0d = %h", uut.dp.rf.wa3, uut.dp.rf.wd3);
            end
        end
    end
    
    // Verify Memory Load at start
    initial begin
        #10; // Wait for reset
        $display("Checking Memory at 0x00...");
        $display("Mem[0] = %h (Should be 00a00093 for ADDI x1, x0, 10)", uut.dp.imem.ram[0]);
        $display("Mem[1] = %h (Should be 01400113 for ADDI x2, x0, 20)", uut.dp.imem.ram[1]);
        $display("Mem[2] = %h (Should be 002081b3 for ADD x3, x1, x2)", uut.dp.imem.ram[2]);
    end

endmodule
