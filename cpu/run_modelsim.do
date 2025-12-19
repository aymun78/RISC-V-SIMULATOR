# ModelSim Script
vlib work

# Compile all Verilog files
vlog alu.v
vlog control_unit.v
vlog cpu.v
vlog data_memory.v
vlog datapath.v
vlog imm_gen.v
vlog instr_memory.v
vlog regfile.v
vlog cpu_tb.v

# Start Simulation
vsim -voptargs=+acc work.cpu_tb

# Add Waves
add wave -noupdate -group "Testbench" sim:/cpu_tb/*
add wave -noupdate -group "CPU Top" sim:/cpu_tb/uut/*
add wave -noupdate -group "Datapath" sim:/cpu_tb/uut/dp/*
add wave -noupdate -group "ALU" sim:/cpu_tb/uut/dp/alu_unit/*
add wave -noupdate -group "Registers" sim:/cpu_tb/uut/dp/rf/*

# Run
run 1000ns
zoom full
