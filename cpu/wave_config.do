# Configure Wave Window
view wave
configure wave -namecolwidth 250
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2

# Clear existing waves
delete wave *

# System Signals
add wave -noupdate -divider "System Signals"
add wave -noupdate -label "Clock" -radix binary sim:/cpu_tb/clk
add wave -noupdate -label "Reset" -radix binary sim:/cpu_tb/reset

# Pipeline Control
add wave -noupdate -divider "Pipeline Control"
add wave -noupdate -label "Instruction Pointer" -radix hex sim:/cpu_tb/uut/dp/PC
add wave -noupdate -label "Instruction" -radix hex sim:/cpu_tb/uut/dp/Instr
# Note: 'Stall' and 'ALU Busy' are not explicitly defined in the current basic datapath, omitting for now.
add wave -noupdate -label "Branch Taken" -radix binary sim:/cpu_tb/uut/dp/PCSrc

# ALU Operations
add wave -noupdate -divider "ALU Operations"
add wave -noupdate -label "ALU Result" -radix hex sim:/cpu_tb/uut/dp/ALUResult
add wave -noupdate -label "ALU Control" -radix binary sim:/cpu_tb/uut/dp/ID_EX_ALUControl

# Registers
add wave -noupdate -divider "Registers"
add wave -noupdate -label "x1" -radix hex sim:/cpu_tb/uut/dp/rf/rf[1]
add wave -noupdate -label "x2" -radix hex sim:/cpu_tb/uut/dp/rf/rf[2]
add wave -noupdate -label "x3" -radix hex sim:/cpu_tb/uut/dp/rf/rf[3]
add wave -noupdate -label "x4" -radix hex sim:/cpu_tb/uut/dp/rf/rf[4]
add wave -noupdate -label "x5" -radix hex sim:/cpu_tb/uut/dp/rf/rf[5]

# Data Memory
add wave -noupdate -divider "Data Memory"
add wave -noupdate -label "Mem[00] (Addr 0)" -radix hex sim:/cpu_tb/uut/dp/dmem/ram[0]
add wave -noupdate -label "Mem[04] (Addr 4)" -radix hex sim:/cpu_tb/uut/dp/dmem/ram[1]
add wave -noupdate -label "Mem[08] (Addr 8)" -radix hex sim:/cpu_tb/uut/dp/dmem/ram[2]

# Run and Zoom
run 1000ns
zoom full
