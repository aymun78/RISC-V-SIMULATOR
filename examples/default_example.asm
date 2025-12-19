# Welcome to RISC-V Simulator!
# Load example programs or write your own

ADDI x1, x0, 10   # Load 10 into x1
ADDI x2, x0, 20   # Load 20 into x2
ADD  x3, x1, x2   # Add x1 and x2
SW   x3, 0(x0)    # Store result in memory
LW   x5, 0(x0)    # Load back to check
