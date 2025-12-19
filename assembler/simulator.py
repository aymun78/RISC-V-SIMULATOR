class RISCVSimulator:
    FETCH, DECODE, EXECUTE, MEMORY, WRITEBACK = range(5)
    STAGE_NAMES = ["FETCH", "DECODE", "EXECUTE", "MEMORY", "WRITEBACK"]

    def __init__(self):
        self.regs = [0] * 32
        self.pc = 0
        self.memory = {} # byte addressable conceptually, but we'll use specific keys
        self.output_log = []
        
        # Pipeline State
        self.stage = self.FETCH
        self.ir = 0 # Instruction Register
        self.imm_i = 0
        self.imm_s = 0
        self.imm_b = 0
        self.imm_u = 0
        self.imm_j = 0
        self.opcode = 0
        self.rd = 0
        self.funct3 = 0
        self.rs1 = 0
        self.rs2 = 0
        self.funct7 = 0
        self.alu_res = 0
        self.mem_data = 0
        self.next_pc = 0
        self.instr_completed = False # Flag to signal completion to GUI
        self.energy = 0.0 # Energy in pJ

    def load_program(self, hex_program):
        self.memory = {}
        addr = 0
        for line in hex_program.split('\n'):
            line = line.strip()
            if not line: continue
            self.memory[addr] = int(line, 16)
            addr += 4
        self.reset()
        
    def reset(self):
        self.regs = [0] * 32
        self.pc = 0
        self.energy = 0.0
        self.stage = self.FETCH
        self.ir = 0
        self.instr_completed = False



    def step(self):
        """
        Executes one pipeline stage.
        Returns:
            bool: True if simulation should continue, False if Halted (stuck in Fetch)
        """
        self.instr_completed = False
        
        if self.stage == self.FETCH:
            if self.pc not in self.memory:
                return False # Halt
            
            self.ir = self.memory[self.pc]
            self.energy += 10.0 # Fetch Energy
            self.stage = self.DECODE
            return True

        elif self.stage == self.DECODE:
            instr = self.ir
            self.opcode = instr & 0x7F
            self.rd = (instr >> 7) & 0x1F
            self.funct3 = (instr >> 12) & 0x7
            self.rs1 = (instr >> 15) & 0x1F
            self.rs2 = (instr >> 20) & 0x1F
            self.funct7 = (instr >> 25) & 0x7F
            
            # Immediate extraction
            self.imm_i = (instr >> 20)
            if self.imm_i >= 2048: self.imm_i -= 4096 
            
            self.imm_s = ((instr >> 25) << 5) | ((instr >> 7) & 0x1F)
            if self.imm_s >= 2048: self.imm_s -= 4096
            
            self.imm_b = ((instr >> 31) << 12) | (((instr >> 7) & 0x01) << 11) | (((instr >> 25) & 0x3F) << 5) | (((instr >> 8) & 0x0F) << 1)
            if self.imm_b >= 4096: self.imm_b -= 8192
            
            self.imm_j = ((instr >> 31) << 20) | (((instr >> 12) & 0xFF) << 12) | (((instr >> 20) & 1) << 11) | (((instr >> 21) & 0x3FF) << 1)
            if self.imm_j >= 1048576: self.imm_j -= 2097152
            

            
            self.energy += 5.0 # Decode Energy
            self.stage = self.EXECUTE
            return True
            
        elif self.stage == self.EXECUTE:
            # Simple ALU logic based on decoded fields
            val1 = self.regs[self.rs1]
            val2 = self.regs[self.rs2]
            
            self.alu_res = 0
            self.next_pc = self.pc + 4 # Default next PC
            
            # R-type
            if self.opcode == 0x33: 
                if self.funct3 == 0x0: 
                    if self.funct7 == 0x20: self.alu_res = val1 - val2 # SUB
                    else: self.alu_res = val1 + val2 # ADD
                elif self.funct3 == 0x7: self.alu_res = val1 & val2 # AND
                elif self.funct3 == 0x6: self.alu_res = val1 | val2 # OR
                elif self.funct3 == 0x4: self.alu_res = val1 ^ val2 # XOR
                elif self.funct3 == 0x1: self.alu_res = (val1 << (val2 & 0x1F)) # SLL
                elif self.funct3 == 0x5: self.alu_res = (val1 >> (val2 & 0x1F)) # SRL
                elif self.funct3 == 0x2: self.alu_res = 1 if val1 < val2 else 0 # SLT
                elif self.funct3 == 0x3: self.alu_res = val1 if val1 > val2 else val2 # MAX
            
            # I-type (ADDI)
            elif self.opcode == 0x13:
                self.alu_res = val1 + self.imm_i
                
            # LW
            elif self.opcode == 0x03:
                self.alu_res = val1 + self.imm_i # Address calculation
                
            # SW
            elif self.opcode == 0x23:
                self.alu_res = val1 + self.imm_s # Address calculation
                
            # BEQ
            elif self.opcode == 0x63:
                if val1 == val2:
                    self.next_pc = self.pc + self.imm_b
                    
            # JAL
            elif self.opcode == 0x6F:
                self.alu_res = self.pc + 4 # Return address
                self.next_pc = self.pc + self.imm_j


            # Energy for Execute (ALU vs Control)
            if self.opcode in [0x63, 0x6F]: # Branch/Jump
                self.energy += 15.0
            else:
                self.energy += 20.0 # Standard ALU

            self.stage = self.MEMORY
            return True

        elif self.stage == self.MEMORY:
            self.mem_data = 0
            
            # LW
            if self.opcode == 0x03:
                addr = self.alu_res & 0xFFFFFFFC
                self.mem_data = self.memory.get(addr, 0)
                
            # SW
            elif self.opcode == 0x23:
                addr = self.alu_res & 0xFFFFFFFC
                self.memory[addr] = self.regs[self.rs2]
            

            
            # Memory Access Energy (High cost for Load/Store)
            if self.opcode in [0x03, 0x23]:
                 self.energy += 100.0
            
            self.stage = self.WRITEBACK
            return True

        elif self.stage == self.WRITEBACK:
            # Write to Register
            if self.rd != 0:
                # ALU result for R-type, ADDI, JAL
                if self.opcode in [0x33, 0x13, 0x6F]:
                     self.regs[self.rd] = self.alu_res & 0xFFFFFFFF
                # Memory data for LW
                elif self.opcode == 0x03:
                     self.regs[self.rd] = self.mem_data
            
            # Update PC
            self.pc = self.next_pc
            self.instr_completed = True
            
            
            self.energy += 5.0 # Writeback Energy
            self.stage = self.FETCH
            return True
            
        return False

    def run(self, cycles=100):
        executed_instrs = 0
        for _ in range(cycles):
            if not self.step():
                break
            if self.instr_completed:
                executed_instrs += 1
        return executed_instrs # Return instruction count for compatibility

    def get_instruction_details(self):
        # Return details based on partial state
        
        status_str = "Running"
        if self.pc not in self.memory and self.stage == self.FETCH:
             status_str = "Halted"

        name = "..."
        type_ = "..."
        
        # Best effort name resolution if we have decoded
        if self.stage >= self.DECODE:
             if self.opcode == 0x33:
                type_ = "R-Type"
                if self.funct3 == 0x0: 
                    name = "SUB" if self.funct7 == 0x20 else "ADD"
                elif self.funct3 == 0x7: name = "AND"
                elif self.funct3 == 0x6: name = "OR"
                elif self.funct3 == 0x4: name = "XOR"
                elif self.funct3 == 0x1: name = "SLL"
                elif self.funct3 == 0x5: name = "SRL"
                elif self.funct3 == 0x2: name = "SLT"
                elif self.funct3 == 0x3: name = "MAX"
             elif self.opcode == 0x13:
                type_ = "I-Type"; name = "ADDI"
             elif self.opcode == 0x03:
                type_ = "I-Type"; name = "LW"
             elif self.opcode == 0x23:
                type_ = "S-Type"; name = "SW"
             elif self.opcode == 0x63:
                type_ = "B-Type"; name = "BEQ"
             elif self.opcode == 0x6F:
                type_ = "J-Type"; name = "JAL"
        
        return {
            "status": status_str,
            "pc": self.pc,
            "stage": self.STAGE_NAMES[self.stage],
            "instr_hex": f"0x{self.ir:08X}",
            "name": name,
            "type": type_,
            "opcode": f"0x{self.opcode:07b}",
            "rd": f"x{self.rd}",
            "rs1": f"x{self.rs1}",
            "rs2": f"x{self.rs2}",
            "imm": f"{self.imm_i}" if type_ == "I-Type" else (f"{self.imm_s}" if type_ == "S-Type" else (f"{self.imm_b}" if type_ == "B-Type" else (f"{self.imm_j}" if type_ == "J-Type" else "0"))),
            "funct3": f"{self.funct3:03b}",
            "funct7": f"{self.funct7:07b}"
        }
