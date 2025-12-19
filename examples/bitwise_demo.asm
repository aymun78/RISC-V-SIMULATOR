# Test AND, OR, XOR
ADDI x1, x0, 15  # 0000 1111
ADDI x2, x0, 10  # 0000 1010
AND x3, x1, x2   # 0000 1010 (10)
OR  x4, x1, x2   # 0000 1111 (15)
XOR x5, x1, x2   # 0000 0101 (5)
