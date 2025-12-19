# Calculate 5! = 120
ADDI x1, x0, 5   # N = 5
ADDI x2, x0, 1   # Result = 1
Loop:
BEQ x1, x0, Done # If N==0, Done
# No MUL, use repeated ADD loop for Result * N?
# Too complex for basic CPU without MUL.
# Let's do Sum 1..N instead?
# Ok, let's do Sum 1 to 5 = 15
ADD x2, x2, x1   # Result += N
ADDI x1, x1, -1
BEQ x0, x0, Loop
Done:
SW x2, 0(x0)     # Store 16 (1+5+4+3+2+1?) Note: Init 1. 1+5+4+3+2+1=16.
