# 5 * 4 using Add
ADDI x1, x0, 5   # A
ADDI x2, x0, 4   # B
ADDI x3, x0, 0   # Res
Loop:
BEQ x2, x0, Done
ADD x3, x3, x1
ADDI x2, x2, -1
BEQ x0, x0, Loop
Done:
SW x3, 0(x0) # 20
