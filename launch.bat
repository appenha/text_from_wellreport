@echo off
:: Well Report Processor — double-click launcher

:: ── Guard: must be run from an extracted folder, not inside a zip ─────────────
if not exist "%~dp0launch.ps1" (
    echo.
    echo  ╔══════════════════════════════════════════════════════════════╗
    echo  ║  PLEASE EXTRACT THE ZIP FIRST                                ║
    echo  ║                                                              ║
    echo  ║  Right-click WellReportProcessor.zip ^> Extract All...       ║
    echo  ║  Then open the extracted folder and double-click             ║
    echo  ║  launch.bat again.                                           ║
    echo  ╚══════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0app.py" (
    echo.
    echo  ERROR: app.py not found next to this launcher.
    echo  Make sure you extracted ALL files from the zip.
    echo.
    pause
    exit /b 1
)

:: ── Run the PowerShell launcher ───────────────────────────────────────────────
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Launcher exited with error code %ERRORLEVEL%.
    pause
)
