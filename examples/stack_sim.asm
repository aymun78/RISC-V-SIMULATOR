# Push/Pop Simulation
ADDI sp, x0, 100 # Stack Pointer at 100
# Push 5
ADDI sp, sp, -4
ADDI x1, x0, 5
SW x1, 0(sp)
# Push 8
ADDI sp, sp, -4
ADDI x5, x0, 8
SW x5, 0(sp)
# Pop into x3 (Should be 8)
LW x3, 0(sp)
ADDI sp, sp, 4
# Pop into x4 (Should be 5)
LW x4, 0(sp)
ADDI sp, sp, 4
