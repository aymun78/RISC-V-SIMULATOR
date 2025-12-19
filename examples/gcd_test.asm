# GCD Test Logic
# x2 = 48, x3 = 18
ADDI x2, x0, 48
ADDI x3, x0, 18
# GCD x1, x2, x3
# Encoded manually as 0x0031008B since assembler likely doesn't support GCD mnemonic yet.
.word 0x0031008B
# Result x1 should be 6
