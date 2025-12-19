@echo off
cd /d "%~dp0"

echo ==========================================
echo      RISC-V ModelSim Verification
echo ==========================================

:: Attempt to find vsim in PATH
where vsim >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] vsim found in PATH.
    set VSIM_CMD=vsim
    goto :COMPILE
)

:: Check Common Paths
if exist "C:\modeltech64_2020.1\win64\vsim.exe" (
    set "VSIM_CMD=C:\modeltech64_2020.1\win64\vsim.exe"
    goto :FOUND
)

if exist "C:\intelFPGA\20.1\modelsim_ase\win32aloem\vsim.exe" (
    set "VSIM_CMD=C:\intelFPGA\20.1\modelsim_ase\win32aloem\vsim.exe"
    goto :FOUND
)

if exist "C:\intelFPGA_lite\20.1\modelsim_ase\win32aloem\vsim.exe" (
    set "VSIM_CMD=C:\intelFPGA_lite\20.1\modelsim_ase\win32aloem\vsim.exe"
    goto :FOUND
)

echo [ERROR] Could not find vsim.exe automatically.
exit /b 1

:FOUND
echo [INFO] Found vsim at: "%VSIM_CMD%"

:COMPILE
echo [INFO] Compiling Verilog files...
if "%VSIM_CMD%"=="vsim" (
    if exist work rmdir /s /q work
    vlib work
    vlog alu.v control_unit.v cpu.v data_memory.v datapath.v imm_gen.v instr_memory.v regfile.v cpu_tb.v
) else (
    "%VSIM_CMD:~0,-8%vlib.exe" work
    "%VSIM_CMD:~0,-8%vlog.exe" alu.v control_unit.v cpu.v data_memory.v datapath.v imm_gen.v instr_memory.v regfile.v cpu_tb.v
)

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation Failed.
    exit /b 1
)

echo [INFO] Running Simulation...
"%VSIM_CMD%" -c -voptargs="+acc=npr" work.cpu_tb -do "run -all; quit"
