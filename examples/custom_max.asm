# Test MAX Instruction
ADDI x1, x0, 50
ADDI x2, x0, 25
MAX x3, x1, x2  # Should be 50
SW x3, 0(x0)
