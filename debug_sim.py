
from assembler.simulator import RISCVSimulator

def test_simulator():
    sim = RISCVSimulator()
    # Program:
    # ADDI x1, x0, 10
    # SW x1, 8(x0)  -> Writes 10 to address 8.
    program_hex = "00A00093\n00102423" 
    # 0x00A00093 = ADDI x1, x0, 10
    # 0x00102423: 
    #   opcode=0x23 (Storage)
    #   funct3=010 (SW)
    #   rs1=0 (x0)
    #   rs2=1 (x1)
    #   imm encoded: bit 11..5 in 31..25, 4..0 in 11..7
    #   imm = 8. binary 0000 0000 1000.
    #   imm[11:5] = 0000000 -> instr[31:25]=0
    #   imm[4:0] = 01000 -> instr[11:7]=01000 (0x8)
    #   rs2 = 00001
    #   rs1 = 00000
    #   funct3 = 010 (2)
    #   opcode = 0100011 (0x23)
    #   Reassemble:
    #   0000000 (imm7) | 00001 (rs2) | 00000 (rs1) | 010 (f3) | 01000 (imm5) | 0100011 (op)
    #   0000 0000 0001 0000 0 010 0100 0 010 0011 -> 0010 2423. Correct.
    
    sim.load_program("00A00093\n00102423")
    print(f"Initial Memory: {sim.memory}")
    
    # Step 1: ADDI
    sim.step()
    print(f"After Step 1: PC={sim.pc}, x1={sim.regs[1]}")
    
    # Step 2: SW
    sim.step()
    print(f"After Step 2: PC={sim.pc}, Memory[8]={sim.memory.get(8, 'Not Found')}")

    # Check Details
    print(f"Details at End: {sim.get_instruction_details()}")

    print("Running Debug Test...")

if __name__ == "__main__":
    test_simulator()
