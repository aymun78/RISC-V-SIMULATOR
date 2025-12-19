@echo off
cd /d "%~dp0"

echo ==========================================
echo      RISC-V ModelSim Launcher
echo ==========================================

:: Attempt to find vsim in PATH
where vsim >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] vsim found in PATH.
    set VSIM_CMD=vsim
    goto :COMPILE
)

:: Check Common Paths
echo [INFO] vsim not in PATH. Checking common locations...

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
echo Please ensure ModelSim is installed and 'vsim' is in your PATH,
echo or edit this batch file to point to your vsim.exe.
echo.
pause
exit /b 1

:FOUND
echo [INFO] Found vsim at: "%VSIM_CMD%"

:COMPILE
echo [INFO] Preparing library...
if "%VSIM_CMD%"=="vsim" (
    if exist work rmdir /s /q work
    vlib work

) else (
    "%VSIM_CMD:~0,-8%vlib.exe" work
)

echo [INFO] Compiling Verilog files...
:: Uses vlog from the same directory as vsim if possible, or assumes in path

:: Basic vlog check
where vlog >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    vlog alu.v control_unit.v cpu.v data_memory.v datapath.v imm_gen.v instr_memory.v regfile.v cpu_tb.v
) else (
    echo [WARN] vlog not in PATH. Attempting to use path relative to vsim...
    "%VSIM_CMD:~0,-8%vlog.exe" alu.v control_unit.v cpu.v data_memory.v datapath.v imm_gen.v instr_memory.v regfile.v cpu_tb.v
)

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation Failed.
    pause
    exit /b 1
)

echo [INFO] Launching Simulation...
start "" "%VSIM_CMD%" -gui -voptargs="+acc=npr" work.cpu_tb -do wave_config.do

echo [SUCCESS] ModelSim launched.
:: Pause briefly then exit
timeout /t 5
