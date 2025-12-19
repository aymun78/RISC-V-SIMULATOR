import sys
import re

# ISA Definitions
# ISA Definitions
OPCODES = {
    'ADD':  {'type': 'R', 'opcode': '0110011', 'funct3': '000', 'funct7': '0000000'},
    'SUB':  {'type': 'R', 'opcode': '0110011', 'funct3': '000', 'funct7': '0100000'},
    'AND':  {'type': 'R', 'opcode': '0110011', 'funct3': '111', 'funct7': '0000000'},
    'OR':   {'type': 'R', 'opcode': '0110011', 'funct3': '110', 'funct7': '0000000'},
    'XOR':  {'type': 'R', 'opcode': '0110011', 'funct3': '100', 'funct7': '0000000'},
    'SLL':  {'type': 'R', 'opcode': '0110011', 'funct3': '001', 'funct7': '0000000'},
    'SRL':  {'type': 'R', 'opcode': '0110011', 'funct3': '101', 'funct7': '0000000'},
    'SLT':  {'type': 'R', 'opcode': '0110011', 'funct3': '010', 'funct7': '0000000'},
    'MAX':  {'type': 'R', 'opcode': '0110011', 'funct3': '011', 'funct7': '0000000'}, # Custom (Remapped)
    'ADDI': {'type': 'I', 'opcode': '0010011', 'funct3': '000'},
    'SLLI': {'type': 'I', 'opcode': '0010011', 'funct3': '001'}, # Shift Immediate
    'SRLI': {'type': 'I', 'opcode': '0010011', 'funct3': '101'},
    'LW':   {'type': 'I', 'opcode': '0000011', 'funct3': '010'}, # Simplified loading
    'SW':   {'type': 'S', 'opcode': '0100011', 'funct3': '010'},
    'BEQ':  {'type': 'B', 'opcode': '1100011', 'funct3': '000'},
    'JAL':  {'type': 'J', 'opcode': '1101111'}
}

REGISTERS = {f'x{i}': i for i in range(32)}
# Add ABI names if needed (zero, ra, sp, etc)
REGISTERS['zero'] = 0
REGISTERS['ra'] = 1
REGISTERS['sp'] = 2
REGISTERS['gp'] = 3
REGISTERS['tp'] = 4
REGISTERS['t0'] = 5
REGISTERS['t1'] = 6
REGISTERS['t2'] = 7
REGISTERS['s0'] = 8
REGISTERS['fp'] = 8
REGISTERS['s1'] = 9 
REGISTERS['a0'] = 10
REGISTERS['a1'] = 11

def to_bin(val, bits):
    val = int(val)
    if val < 0:
        val = (1 << bits) + val
    return f"{val:0{bits}b}"

def assemble_line(line, pc, labels):
    # Remove comments and strip
    line = line.split('#')[0].strip()
    if not line or line.endswith(':'): return None
    
    parts = line.replace(',', ' ').split()
    instr = parts[0].upper()
    args = parts[1:]
    
    if instr not in OPCODES:
        raise ValueError(f"Unknown instruction: {instr} at PC {pc}")
    
    op_def = OPCODES[instr]
    fmt = op_def['type']
    opcode = op_def['opcode']
    
    bin_instr = ""
    
    try:
        if fmt == 'R':
            rd = REGISTERS[args[0]]
            rs1 = REGISTERS[args[1]]
            rs2 = REGISTERS[args[2]]
            bin_instr = f"{op_def['funct7']}{to_bin(rs2,5)}{to_bin(rs1,5)}{op_def['funct3']}{to_bin(rd,5)}{opcode}"
            
        elif fmt == 'I':
            rd = REGISTERS[args[0]]
            # LW logic: LW x1, 0(x2) or LW x1, 0(sp)
            if instr == 'LW':
                match = re.match(r'(-?\d+)\((\w+)\)', args[1]) # \w+ matches sp, x2, etc
                if not match: raise ValueError(f"Invalid LW format: {args[1]}")
                imm = int(match.group(1))
                rs1 = REGISTERS[match.group(2)]
            else:
                rs1 = REGISTERS[args[1]]
                imm = int(args[2])
            
            bin_instr = f"{to_bin(imm, 12)}{to_bin(rs1,5)}{op_def['funct3']}{to_bin(rd,5)}{opcode}"

        elif fmt == 'S':
            # SW x1, 0(x2) -> src=x1, base=x2
            rs2 = REGISTERS[args[0]]
            match = re.match(r'(-?\d+)\((\w+)\)', args[1])
            if not match: raise ValueError(f"Invalid SW format: {args[1]}")
            imm = int(match.group(1))
            rs1 = REGISTERS[match.group(2)]
            
            imm_bin = to_bin(imm, 12)
            bin_instr = f"{imm_bin[:7]}{to_bin(rs2,5)}{to_bin(rs1,5)}{op_def['funct3']}{imm_bin[7:]}{opcode}"

        elif fmt == 'B': # BEQ rs1, rs2, label
            rs1 = REGISTERS[args[0]]
            rs2 = REGISTERS[args[1]]
            label = args[2]
            
            if label in labels:
                offset = labels[label] - pc
            else:
                offset = int(label) # allow raw offsets
            
            imm_bin = to_bin(offset >> 1, 12) # immediate is encoded as multiples of 2 bytes, but here we just follow standard encoding theory which usually drops LSB.
            # But wait, standard B-type immediate structure is weird: imm[12|10:5|4:1|11]
            # Simplifying: Let's just output the 32-bit hex and let Verilog imm_gen handle it?
            # My imm_gen expects standard B-type shuffling: {{20{Instr[31]}}, Instr[7], Instr[30:25], Instr[11:8], 1'b0}
            # So I must encode it correctly here.
            
            # offset is byte difference. 
            pass # TODO: Implement complex B-type shuffling if rigorous. 
            # For this simple assembler, let's do a basic shuffle.
            # imm[12] is bit 12 of offset.
            val = int(offset)
            if val < 0: val = (1<<13) + val
            
            # Bits: 12, 11, 10...1
            b = f"{val:013b}"
            # b has 13 bits (indices 0 to 12).
            # imm[12] = b[0]
            # imm[11] = b[1]
            # imm[10:5] = b[2:8]
            # imm[4:1] = b[8:12]
            
            imm12 = b[0]
            imm11 = b[1]
            imm10_5 = b[2:8]
            imm4_1 = b[8:12]
            
            bin_instr = f"{imm12}{imm10_5}{to_bin(rs2,5)}{to_bin(rs1,5)}{op_def['funct3']}{imm4_1}{imm11}{opcode}"

        elif fmt == 'J': # JAL rd, label
            rd = REGISTERS[args[0]]
            label = args[1]
            
            if label in labels:
                offset = labels[label] - pc
            else:
                offset = int(label)
                
            val = int(offset)
            if val < 0: val = (1<<21) + val
            b = f"{val:021b}" # 21 bits
            
            # J-type: imm[20|10:1|11|19:12]
            imm20 = b[0]
            imm10_1 = b[10:20] # Wait, bits 10 down to 1. 21 bits are 20..0. b[0]=bit20. b[1]=bit19.
            # b = [20, 19, 18, ..., 1, 0]
            # imm20 = b[0]
            # imm19_12 = b[1:9]
            # imm11 = b[9]
            # imm10_1 = b[10:20]
            
            imm20 = b[0]
            imm19_12 = b[1:9]
            imm11 = b[9]
            imm10_1 = b[10:20]

            bin_instr = f"{imm20}{imm10_1}{imm11}{imm19_12}{to_bin(rd,5)}{opcode}"
            
    except Exception as e:
        raise ValueError(f"Error assembling {line}: {str(e)}")
        
    return f"{int(bin_instr, 2):08x}"

def assemble_program(source_code):
    """
    Assembles the full source code.
    Returns:
        tuple: (hex_string, labels_dict, instr_map)
        hex_string: Newline separated hex codes
        labels_dict: Mapping of Label -> PC
        instr_map: List of dicts [{'pc': pc, 'src': source_line}]
    """
    lines = source_code.split('\n')
    labels = {}
    pc = 0
    clean_lines = []
    instr_map = [] 
    
    # First Pass: Label Resolution & Cleanup
    for line in lines:
        # Strip comments immediately to avoid parsing ':' in comments as labels
        line = line.split('#')[0].strip()
        if not line: continue
        
        if line.endswith(':'):
            labels[line[:-1]] = pc
        elif ':' in line: # label: instruction
            parts = line.split(':')
            labels[parts[0].strip()] = pc
            cleaned = parts[1].strip()
            if cleaned:
                clean_lines.append(cleaned)
                instr_map.append({'pc': pc, 'src': cleaned})
                pc += 4
        else:
            clean_lines.append(line)
            instr_map.append({'pc': pc, 'src': line})
            pc += 4
            
    # Second Pass: Assembly
    hex_codes = []
    current_pc = 0 # Track PC for assembly errors
    for line in clean_lines:
        hex_code = assemble_line(line, current_pc, labels)
        if hex_code:
            hex_codes.append(hex_code)
            current_pc += 4
            
    return "\n".join(hex_codes), labels, instr_map

def main():
    if len(sys.argv) < 2:
        print("Usage: assembler.py <input.asm> [output.hex]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = "program.hex" if len(sys.argv) < 3 else sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
            
        hex_output, labels, _ = assemble_program(source_code)
        
        with open(output_file, 'w') as f:
            f.write(hex_output + '\n')
            
        print(f"Success! Output written to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
