# Memory Read/Write
ADDI x1, x0, 100
SW x1, 0(x0)    # Mem[0] = 100
SW x1, 4(x0)    # Mem[4] = 100
LW x2, 0(x0)
ADD x3, x2, x2
SW x3, 8(x0)    # Mem[8] = 200
