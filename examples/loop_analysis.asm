# Loop 1 to 5
ADDI x1, x0, 0   # Sum
ADDI x2, x0, 1   # Counter
ADDI x3, x0, 6   # Limit
Loop:
ADD x1, x1, x2   # Sum += Counter
ADDI x2, x2, 1   # Counter++
BEQ x2, x3, Exit # If Counter == 6, Exit
BEQ x0, x0, Loop # Jump back
Exit:
SW x1, 0(x0)     # Store Sum
