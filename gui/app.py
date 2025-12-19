import streamlit as st
import sys
import os
import pandas as pd
import time
import copy

# Add repo root to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from assembler.assembler import assemble_program
from assembler.simulator import RISCVSimulator

st.set_page_config(layout="wide", page_title="RISC-V Simulator", initial_sidebar_state="expanded")

# --- Custom CSS for Dashboard Look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code:wght@400;500&display=swap');

    /* Global Theme */
    .stApp {
        background-color: #0d1117;
        font-family: 'Inter', sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #e6edf3 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar */
    div[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Cards/Containers */
    .dashboard-card, div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px; # Pill shape
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #30363d;
        border-color: #8b949e;
        color: #ffffff;
    }
    .stButton > button:active {
        background-color: #238636;
        border-color: #2ea043;
        color: #ffffff;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-family: 'Fira Code', monospace;
        color: #58a6ff;
        font-size: 1.8rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
        font-size: 0.9rem !important;
    }
    
    /* Tables/Dataframes */
    .stDataFrame {
        border: 1px solid #30363d;
        border-radius: 6px;
    }
    
    /* Inputs */
    .stTextArea textarea {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
        font-family: 'Fira Code', monospace;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #161b22;
        border-color: #30363d;
        color: #c9d1d9;
    }
    
    /* Custom Classes for Injection */
    .machine-cycle-active {
        color: #2ea043; 
        font-weight: bold;
        border: 1px solid #2ea043;
        background: rgba(46, 160, 67, 0.1);
        padding: 4px 8px;
        border-radius: 4px;
    }
    .machine-cycle-idle {
        color: #8b949e;
        border: 1px solid #30363d;
        padding: 4px 8px;
        border-radius: 4px;
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1117; 
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #8b949e; 
    }
    
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'simulator' not in st.session_state:
    st.session_state['simulator'] = RISCVSimulator()
    st.session_state['assembled_hex'] = ""
    st.session_state['last_regs'] = [0] * 32
    st.session_state['labels'] = {}
    st.session_state['status_msg'] = "Ready"
    st.session_state['instr_map'] = [] # List of (address, original_line) for highlighting
    st.session_state['run_metrics'] = {'cycles': 0, 'instrs': 0}

if 'asm_code' not in st.session_state:
    st.session_state['asm_code'] = """# Welcome to RISC-V Simulator!
# Load example programs or write your own

ADDI x1, x0, 10   # Load 10 into x1
ADDI x2, x0, 20   # Load 20 into x2
ADD  x3, x1, x2   # Add x1 and x2
SW   x3, 0(x0)    # Store result in memory
LW   x5, 0(x0)    # Load back to check
"""

# --- Header ---
st.title("🖥️ RISC-V Simulator")
st.caption("Educational CPU Architecture Simulator")
st.markdown("---")

# --- Sidebar: Info & Cheatsheet ---
with st.sidebar:
    st.header("ℹ️ Supported Instructions")
    st.markdown("""
    **Arithmetic/Logic (R-Type)**:
    - `ADD`, `SUB`, `AND`, `OR`
    - `XOR`, `SLL`, `SRL` (New!)
    - `SLT` (Set Less Than)
    - `MAX` (Custom)
    
    **Immediate (I-Type)**:
    - `ADDI`, `LW`
    
    **Control/Mem**:
    - `SW` (Store)
    - `BEQ` (Branch Equal)
    - `JAL` (Jump & Link)
    """)
    st.markdown("---")


# --- Top Dashboard Row ---
# Use columns to create the card layout
col_ctrl, col_cycle, col_status, col_pc = st.columns(4)

sim = st.session_state['simulator']

# 1. Execution Controls
with col_ctrl:
    st.markdown("### ● Execution Controls")
    c1, c2, c3 = st.columns(3)
    if c1.button("▶ Run", use_container_width=True):
        st.session_state['last_regs'] = list(sim.regs)
        
        # --- ModelSim Integration ---
        if st.session_state['assembled_hex']:
            try:
                hex_path = os.path.join(os.path.dirname(__file__), '..', 'cpu', 'program.hex')
                with open(hex_path, "w") as f:
                     f.write(st.session_state['assembled_hex'])
                
                # Trigger ModelSim (System Call)
                bat_path = os.path.join(os.path.dirname(__file__), '..', 'run_simulation.bat')
                
                # Use os.system with 'start' to launch independently
                command = f'start "" "{bat_path}"'
                os.system(command)
                
                st.toast("ModelSim Launched! 🚀")
            except Exception as e:
                st.error(f"Launch Error: {e}")
        # ----------------------------

        # Run 100 cycles
        executed_instrs = sim.run(100)
        st.session_state['run_metrics']['cycles'] += 100
        st.session_state['run_metrics']['instrs'] += executed_instrs
        st.rerun()
        
    if c2.button("⏯ Step", use_container_width=True):
        st.session_state['last_regs'] = list(sim.regs)
        if sim.step():
            st.session_state['status_msg'] = f"Stage: {sim.STAGE_NAMES[sim.stage]}"
            st.session_state['run_metrics']['cycles'] += 1
            if sim.instr_completed:
                st.session_state['run_metrics']['instrs'] += 1
        st.rerun()
        
    if c3.button("↺ Reset", use_container_width=True):
         if st.session_state['assembled_hex']:
             st.session_state['simulator'].load_program(st.session_state['assembled_hex'])
             st.session_state['simulator'].regs = [0] * 32
             st.session_state['simulator'].pc = 0
             st.session_state['run_metrics'] = {'cycles': 0, 'instrs': 0}
             st.session_state['last_regs'] = [0] * 32
             st.success("Simulation Reset")
             st.rerun()
         
    speed = 0.1
    if st.button("Auto-Play", use_container_width=True):
        place = st.empty()
        with place.container():
            st.info("Running...")
        for _ in range(20):
             st.session_state['last_regs'] = list(sim.regs)
             if not sim.step(): break
             st.session_state['run_metrics']['cycles'] += 1
             if sim.instr_completed:
                 st.session_state['run_metrics']['instrs'] += 1
             time.sleep(speed)
        st.rerun()

# 2. Machine Cycle (Visual Only)
with col_cycle:
    st.markdown("### ● Machine Cycle")
    # Determine phase based on some logic or just show IDLE/EXEC check
    phase = "IDLE" if sim.pc not in sim.memory else "EXECUTE"
    phase_class = "machine-cycle-active" if phase == "EXECUTE" else "machine-cycle-idle"
    
    st.markdown(f"""
    <div class="{phase_class}" style="text-align: center; margin-bottom: 12px;">
        <div style="font-size:0.8em; opacity:0.8">SYSTEM STATE</div>
        <div style="font-size:1.2em; font-weight:bold;">{phase}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("Pipeline Stages")
    cols = st.columns(5)
    labels = ["IF", "ID", "EX", "MEM", "WB"]
    tooltips = ["Instruction Fetch", "Instruction Decode", "Execute", "Memory Access", "Write Back"]
    
    for i, l in enumerate(labels):
        # Highlight based on current stage
        is_active = (sim.stage == i)
        bg = "#1f6feb" if is_active else "transparent"
        border = "#1f6feb" if is_active else "#30363d"
        opacity = "1.0" if is_active else "0.4"
        
        cols[i].markdown(f"""
        <div style='background:{bg}; border: 1px solid {border}; color: #e6edf3; opacity: {opacity}; text-align:center; border-radius:4px; padding:4px; font-size: 0.8em; font-weight: 600;' title='{tooltips[i]}'>
            {l}
        </div>
        """, unsafe_allow_html=True)

# 3. Machine Status
with col_status:
    st.markdown("### 📈 Machine Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("Instructions", st.session_state['run_metrics']['instrs'])
    c2.metric("Cycles", st.session_state['run_metrics']['cycles'])
    c3.metric("CPI", "1.00")
    
    delta_time_ns = st.session_state['run_metrics']['cycles'] * 20 # 50 MHz = 20ns
    total_energy_pj = sim.energy
    
    c4, c5 = st.columns(2)
    if delta_time_ns < 1000:
        c4.metric("Total Time", f"{delta_time_ns} ns")
    elif delta_time_ns < 1000000:
        c4.metric("Total Time", f"{delta_time_ns/1000:.2f} µs")
    else:
        c4.metric("Total Time", f"{delta_time_ns/1e6:.2f} ms")
        
    if total_energy_pj < 1000:
        c5.metric("Total Energy", f"{total_energy_pj:.0f} pJ")
    else:
        c5.metric("Total Energy", f"{total_energy_pj/1000:.2f} nJ")

# 4. Program Counter
with col_pc:
    st.markdown("### 📍 Addressing")
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="color:#8b949e; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px;">Program Counter</div>
        <div style="color:#f2cc60; font-size: 1.8em; font-family:'Fira Code', monospace; margin: 8px 0;">0x{sim.pc:08X}</div>
        <div style="color:#8b949e; font-size: 0.8em; border-top: 1px solid #30363d; padding-top: 8px;">
            <span style="display:inline-block; width: 8px; height: 8px; background-color: #238636; border-radius: 50%; margin-right: 4px;"></span>
            Next: <span style="font-family:'Fira Code', monospace; color: #c9d1d9">0x{sim.pc+4:08X}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Main Content Split ---
col_left, col_right = st.columns([1.5, 1])

# --- LEFT: Assembly & Parsed Instructions ---
with col_left:
    st.markdown("### ● Assembly Code")
    
    # Load Examples from Directory
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    examples = {}
    
    # Ensure directory exists
    if os.path.exists(examples_dir):
        for filename in sorted(os.listdir(examples_dir)):
            if filename.endswith(".asm"):
                with open(os.path.join(examples_dir, filename), "r") as f:
                    examples[filename] = f.read()
    
    # Fallback if empty (shouldn't happen if we populated it)
    if not examples:
        examples["Default"] = st.session_state['asm_code']

    
    
    # Auto-load logic
    example_names = list(examples.keys())
    # Default to first if not set
    if 'current_example' not in st.session_state:
        st.session_state['current_example'] = example_names[0] if example_names else None

    # Selector
    selected_example = st.selectbox(
        "Load Example", 
        example_names, 
        index=example_names.index(st.session_state['current_example']) if st.session_state['current_example'] in example_names else 0,
        key='example_selector',
        label_visibility="collapsed"
    )

    # Detect Change
    if selected_example != st.session_state['current_example']:
        st.session_state['current_example'] = selected_example
        code_content = examples[selected_example]
        st.session_state['asm_code'] = code_content
        st.session_state['editor'] = code_content
        
        # Auto-Build logic
        try:
            hex_output, labels, instr_map = assemble_program(code_content)
            st.session_state['simulator'] = RISCVSimulator()
            st.session_state['simulator'].load_program(hex_output)
            st.session_state['assembled_hex'] = hex_output
            st.session_state['labels'] = labels
            st.session_state['instr_map'] = instr_map
            st.session_state['run_metrics'] = {'cycles': 0, 'instrs': 0}
            st.success(f"Loaded and Built {selected_example}")
        except Exception as e:
            st.error(f"Error building {selected_example}: {e}")
            
        st.rerun()

    # Init editor state if missing
    if 'editor' not in st.session_state:
        st.session_state['editor'] = st.session_state['asm_code']

    # Text Area with Key (removes warning)
    new_code = st.text_area(
        "Write Assembly", 
        key="editor", 
        height=250, 
        label_visibility="collapsed"
    )
    
    # Sync back to asm_code
    if new_code != st.session_state['asm_code']:
        st.session_state['asm_code'] = new_code

    if st.button("🔨 Build & Load", use_container_width=True):
        try:
            # Use shared assembler logic
            hex_output, labels, instr_map = assemble_program(new_code)
            
            # Reset
            st.session_state['simulator'] = RISCVSimulator()
            st.session_state['simulator'].load_program(hex_output)
            st.session_state['assembled_hex'] = hex_output
            st.session_state['labels'] = labels
            st.session_state['instr_map'] = instr_map
            st.session_state['run_metrics'] = {'cycles': 0, 'instrs': 0}
            st.success("Built Successfully!")
            st.rerun()
        except Exception as e:
            st.error(str(e))
            
    if st.button("💾 Export to ModelSim (cpu/program.hex)", use_container_width=True):
        if st.session_state['assembled_hex']:
            try:
                hex_path = os.path.join(os.path.dirname(__file__), '..', 'cpu', 'program.hex')
                with open(hex_path, "w") as f:
                    # Write plain hex lines, Verilog readmemh friendly
                    f.write(st.session_state['assembled_hex'])
                st.success(f"Exported to {hex_path}")
            except Exception as e:
                st.error(f"Export Failed: {e}")
        else:
            st.warning("Assemble first!")

    # Parsed Instructions Table
    st.subheader("Parsed Instructions")
    if st.session_state['instr_map']:
        # Create a DataFrame for display
        data = []
        for item in st.session_state['instr_map']:
            is_active = (item['pc'] == sim.pc)
            marker = "⬅ PC" if is_active else ""
            data.append({
                "Address": f"0x{item['pc']:04X}",
                "Instruction": item['src'],
                "Active": marker
            })
        
        df = pd.DataFrame(data)
        
        # Highlight Logic (using style if possible, or simple dataframe)
        # Streamlit dataframe styling is limited but we can try basic highlighting
        # For now, just showing the dataframe.
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- RIGHT: Registers & Memory ---
with col_right:
    st.markdown("### ● Registers")
    
    # Define a cleaner layout for registers
    # Create 32 items in a scrollable container?
    # Or just a concise dataframe
    
    reg_data = []
    for i in range(32):
        val = sim.regs[i]
        last = st.session_state['last_regs'][i]
        
        diff_style = "color: #f2cc60; font-weight: bold;" if val != last else "color: #8b949e;"
        
        reg_name = f"x{i}"
        alias = ["zero","ra","sp","gp","tp","t0","t1","t2","s0","s1","a0","a1","a2","a3","a4","a5","a6","a7","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11","t3","t4","t5","t6"][i]
        
        reg_data.append({
            "Name": f"{reg_name} ({alias})",
            "Value": f"0x{val:08X}"
        })
        
    st.dataframe(pd.DataFrame(reg_data), height=400, use_container_width=True, hide_index=True)
    
    st.markdown("### ● Memory")
    mem_data = []
    for addr in sorted(sim.memory.keys()):
        mem_data.append({
            "Addr": f"0x{addr:08X}",
            "Val": f"0x{sim.memory[addr]:08X}"
        })
    if mem_data:
        st.dataframe(pd.DataFrame(mem_data), height=200, use_container_width=True, hide_index=True)
    else:
        st.info("Memory Empty")

# --- Details Tab (Bottom) ---
with st.expander("Instruction Decode Details", expanded=True):
    details = sim.get_instruction_details()
    
    if details['status'] == 'Running':
        st.markdown(f"### Current Instruction: **{details.get('name')}**")
        st.markdown(f"**Type**: {details.get('type')}")
        
        # Visual breakdown
        itype = details.get('type')
        
        # Helper to display field
        def field_box(label, value, bits, color="#1f6feb"):
            return f"""
            <div style="
                background-color: rgba(33, 38, 45, 0.8);
                border: 1px solid {color};
                border-top: 3px solid {color};
                padding: 8px; 
                border-radius: 4px; 
                text-align: center; 
                margin: 4px;
                flex: {bits};
                min-width: 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            ">
                <div style="font-size: 0.7em; color: #8b949e; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">{label} <span style="opacity:0.5">({bits})</span></div>
                <div style="font-weight: 600; font-family: 'Fira Code', monospace; color: #e6edf3; font-size: 0.9em; overflow: hidden; white-space: nowrap;">{value}</div>
            </div>
            """
            
        # Display bits
        st.caption(f"Binary: {details.get('instr_hex')} ({int(details.get('instr_hex', '0'), 16):032b})")
        
        cols_html = '<div style="display: flex; width: 100%; overflow-x: auto;">'
        
        # Opcode is always last 7 bits
        opcode_box = field_box("OPCODE", details.get('opcode'), 7, "#d2a8ff")
        rd_box = field_box("RD", details.get('rd'), 5, "#f2cc60")
        funct3_box = field_box("F3", details.get('funct3'), 3, "#58a6ff")
        rs1_box = field_box("RS1", details.get('rs1'), 5, "#ff7b72")
        rs2_box = field_box("RS2", details.get('rs2'), 5, "#eda619")
        funct7_box = field_box("F7", details.get('funct7'), 7, "#3fb950")
        
        if itype == "R-Type":
            cols_html += funct7_box + rs2_box + rs1_box + funct3_box + rd_box + opcode_box
        elif itype == "I-Type":
            # Extract imm: top 12 bits
            imm_val = (int(details.get('instr_hex', '0'), 16) >> 20) & 0xFFF
            cols_html += field_box("IMM", f"0x{imm_val:X}", 12, "#79c0ff") + rs1_box + funct3_box + rd_box + opcode_box
        elif itype == "S-Type":
             cols_html += field_box("IMM1", "...", 7, "#79c0ff") + rs2_box + rs1_box + funct3_box + field_box("IMM2", "...", 5, "#79c0ff") + opcode_box
        elif itype == "B-Type":
             cols_html += field_box("IMM1", "...", 7, "#79c0ff") + rs2_box + rs1_box + funct3_box + field_box("IMM2", "...", 5, "#79c0ff") + opcode_box
        elif itype == "J-Type":
             cols_html += field_box("IMM", "...", 20, "#79c0ff") + rd_box + opcode_box
        else:
             cols_html += field_box("UNKNOWN", "...", 32, "#8b949e")
             
        cols_html += "</div>"
        st.markdown(cols_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Detailed Values
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Opcode", details.get('opcode', '-'))
        c2.metric("Func3", details.get('funct3', '-'))
        c3.metric("RS1", details.get('rs1', '-'))
        c4.metric("RS2", details.get('rs2', '-') if details.get('type') in ["R-Type", "S-Type", "B-Type"] else "-")
        
        st.markdown("#### Instruction Format Sizes")
        fmt_data = []
        # Base fields valid for most
        fmt_data.append({"Field": "Opcode", "Size (Bits)": 7, "Value": details.get('opcode'), "Description": "Operation Code"})
        
        if itype == "R-Type":
            fmt_data.append({"Field": "RD", "Size (Bits)": 5, "Value": details.get('rd'), "Description": "Destination Register"})
            fmt_data.append({"Field": "Funct3", "Size (Bits)": 3, "Value": details.get('funct3'), "Description": "Function 3"})
            fmt_data.append({"Field": "RS1", "Size (Bits)": 5, "Value": details.get('rs1'), "Description": "Source Register 1"})
            fmt_data.append({"Field": "RS2", "Size (Bits)": 5, "Value": details.get('rs2'), "Description": "Source Register 2"})
            fmt_data.append({"Field": "Funct7", "Size (Bits)": 7, "Value": details.get('funct7'), "Description": "Function 7"})
        elif itype == "I-Type":
            fmt_data.append({"Field": "RD", "Size (Bits)": 5, "Value": details.get('rd'), "Description": "Destination Register"})
            fmt_data.append({"Field": "Funct3", "Size (Bits)": 3, "Value": details.get('funct3'), "Description": "Function 3"})
            fmt_data.append({"Field": "RS1", "Size (Bits)": 5, "Value": details.get('rs1'), "Description": "Source Register 1"})
            fmt_data.append({"Field": "Immediate", "Size (Bits)": 12, "Value": details.get('imm'), "Description": "Immediate Value"})
        elif itype == "S-Type":
             fmt_data.append({"Field": "Imm[4:0]", "Size (Bits)": 5, "Value": "...", "Description": "Immediate (Low)"})
             fmt_data.append({"Field": "Funct3", "Size (Bits)": 3, "Value": details.get('funct3'), "Description": "Function 3"})
             fmt_data.append({"Field": "RS1", "Size (Bits)": 5, "Value": details.get('rs1'), "Description": "Base Address Reg"})
             fmt_data.append({"Field": "RS2", "Size (Bits)": 5, "Value": details.get('rs2'), "Description": "Source Register"})
             fmt_data.append({"Field": "Imm[11:5]", "Size (Bits)": 7, "Value": "...", "Description": "Immediate (High)"})
        elif itype == "B-Type":
             fmt_data.append({"Field": "Imm[11|4:1]", "Size (Bits)": 5, "Value": "...", "Description": "Branch Offset (Low)"})
             fmt_data.append({"Field": "Funct3", "Size (Bits)": 3, "Value": details.get('funct3'), "Description": "Branch Condition"})
             fmt_data.append({"Field": "RS1", "Size (Bits)": 5, "Value": details.get('rs1'), "Description": "Source Register 1"})
             fmt_data.append({"Field": "RS2", "Size (Bits)": 5, "Value": details.get('rs2'), "Description": "Source Register 2"})
             fmt_data.append({"Field": "Imm[12|10:5]", "Size (Bits)": 7, "Value": "...", "Description": "Branch Offset (High)"})
        elif itype == "J-Type":
             fmt_data.append({"Field": "RD", "Size (Bits)": 5, "Value": details.get('rd'), "Description": "Return Address Reg"})
             fmt_data.append({"Field": "Immediate", "Size (Bits)": 20, "Value": details.get('imm'), "Description": "Jump Target Offset"})
             
        st.dataframe(pd.DataFrame(fmt_data), use_container_width=True, hide_index=True)
        
        instr_str = f"{details.get('name')} {details.get('rd')}, {details.get('rs1')}, {details.get('rs2')}"
        if details.get('type') == "I-Type":
             if details.get('name') == "LW":
                 instr_str = f"{details.get('name')} {details.get('rd')}, {details.get('imm')}({details.get('rs1')})"
             else:
                 instr_str = f"{details.get('name')} {details.get('rd')}, {details.get('rs1')}, {details.get('imm')}"
        elif details.get('type') == "S-Type":
             instr_str = f"{details.get('name')} {details.get('rs2')}, {details.get('imm')}({details.get('rs1')})"
        elif details.get('type') == "B-Type":
             instr_str = f"{details.get('name')} {details.get('rs1')}, {details.get('rs2')}, {details.get('imm')}"
        elif details.get('type') == "J-Type":
             instr_str = f"{details.get('name')} {details.get('rd')}, {details.get('imm')}"
             
        st.markdown(f"**Instruction**: `{instr_str}` ({details.get('type')})")

    else:
        st.info("Execution Finished. Press 'Reset' to start over.")
