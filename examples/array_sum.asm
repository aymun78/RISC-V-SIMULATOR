# Sum Array [10, 20, 30]
ADDI x1, x0, 10
SW x1, 0(x0)
ADDI x1, x0, 20
SW x1, 4(x0)
ADDI x1, x0, 30
SW x1, 8(x0)
# Sum Logic
ADDI x2, x0, 0 # Sum
ADDI x3, x0, 0 # Addr
ADDI x4, x0, 3 # Count
Loop:
LW x5, 0(x3)   # Load
ADD x2, x2, x5 # Accumulate
ADDI x3, x3, 4 # Next Addr
ADDI x4, x4, -1
BEQ x4, x0, Exit
BEQ x0, x0, Loop
Exit:
SW x2, 12(x0)  # Store Sum (60)
