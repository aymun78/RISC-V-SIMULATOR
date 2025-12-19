# Fibonacci: 0, 1, 1, 2, 3
ADDI x1, x0, 0   # F0
ADDI x2, x0, 1   # F1
SW x1, 0(x0)     # Store F0
SW x2, 4(x0)     # Store F1
ADDI x3, x0, 0   # Addr Offset
ADDI x4, x0, 3   # Count (remaining)
Loop:
ADD x5, x1, x2   # next = F(n-1) + F(n-2)
ADDI x1, x2, 0   # Move F1 -> F0
ADDI x2, x5, 0   # Move Next -> F1
ADDI x3, x3, 4   # Inc Addr
SW x5, 8(x3)     # Store (starts at offset 8)
ADDI x4, x4, -1  # Dec Count
BEQ x4, x0, Done
BEQ x0, x0, Loop
Done:
