@echo off
setlocal EnableExtensions

rem One-click VenusA+WS63 burn entry for the tools\VenusA+WS63 folder.
rem Usage:
rem   run.bat [firmware-root] [--skip-venusa|--skip-ws63|--dry-run]
rem If firmware-root is omitted, the newest ..\fw\Midea_VenusA_WS63_* folder is used.

chcp 936 >nul
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

rem Polaris current bench defaults: AP/VenusA COM11, WS63/upper COM12, control COM13.
set "CONTROL_PORT=COM13"
set "VENUSA_PORT=COM11"
set "WS63_PORT=COM12"

for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "DEFAULT_FW_DIR=%REPO_ROOT%\tools\fw"
set "FIRMWARE_ROOT=%~1"
set "EXTRA_ARGS="

if "%FIRMWARE_ROOT%"=="" goto find_fw
if "%FIRMWARE_ROOT:~0,2%"=="--" (
    set "EXTRA_ARGS=%*"
    set "FIRMWARE_ROOT="
    goto find_fw
)
set "EXTRA_ARGS=%~2 %~3 %~4 %~5 %~6 %~7 %~8 %~9"
goto validate_fw

:find_fw
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "$p='%DEFAULT_FW_DIR%'; $paths=@($p,(Join-Path $p 'extracted')); Get-ChildItem -Directory -Path $paths -Filter 'Midea_VenusA_WS63_*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"`) do set "FIRMWARE_ROOT=%%D"

:validate_fw
if not defined FIRMWARE_ROOT (
    echo [ERROR] No firmware root found. Pass firmware folder path as the first argument.
    echo [ERROR] Looked under: %DEFAULT_FW_DIR%
    pause
    exit /b 1
)
if not exist "%FIRMWARE_ROOT%" (
    echo [ERROR] Firmware root not found: %FIRMWARE_ROOT%
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python was not found in PATH.
    pause
    exit /b 1
)

echo FirmwareRoot : %FIRMWARE_ROOT%
echo ControlPort  : %CONTROL_PORT%
echo VenusAPort   : %VENUSA_PORT%
echo WS63Port     : %WS63_PORT%
echo ExtraArgs    : %EXTRA_ARGS%
echo.
echo Real burn starts now. Close other serial tools before continuing.
echo.

python -u .\auto_burn.py --firmware-root "%FIRMWARE_ROOT%" --control-port %CONTROL_PORT% --venusa-port %VENUSA_PORT% --ws63-port %WS63_PORT% %EXTRA_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Burn script exited with code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
