# Test SLL, SRL
ADDI x1, x0, 1
SLLI x2, x1, 2    # 1 << 2 = 4
SLLI x3, x1, 3    # 1 << 3 = 8
ADDI x4, x0, 16
SRLI x5, x4, 2    # 16 >> 2 = 4
