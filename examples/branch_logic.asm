# Complex Branching
ADDI x1, x0, 5
ADDI x2, x0, 10
BEQ x1, x2, Eq   # Should not take
ADDI x3, x0, 1   # x3 = 1
BEQ x0, x0, Skip
Eq:
ADDI x3, x0, 2
Skip:
ADDI x4, x3, 1   # x4 = 2
