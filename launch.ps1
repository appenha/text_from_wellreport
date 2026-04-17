# Well Report Processor - Launcher
# Ensures uv is available, then runs the app with all dependencies resolved.

# Always work from the folder that contains this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = Get-Location }
Set-Location $scriptDir

trap {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Well Report Processor" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Locate uv ---

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue

if (-not $uvCmd) {
    # Check well-known install locations left by the official installer
    $candidates = @(
        "$env:LOCALAPPDATA\astral-sh\uv\bin\uv.exe"
        "$env:USERPROFILE\.local\bin\uv.exe"
        "$env:LOCALAPPDATA\uv\bin\uv.exe"
        "$env:APPDATA\uv\bin\uv.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $env:PATH = (Split-Path $candidate) + ";$env:PATH"
            $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
            break
        }
    }
}

# --- 2. Install uv if still not found ---

if (-not $uvCmd) {
    Write-Host "uv not found - installing now (one-time setup)..." -ForegroundColor Yellow
    Write-Host ""
    try {
        Invoke-Expression (Invoke-RestMethod "https://astral.sh/uv/install.ps1")
    } catch {
        Write-Host "Automatic install failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install uv manually:" -ForegroundColor Yellow
        Write-Host "  winget install astral-sh.uv" -ForegroundColor White
        Write-Host "Then re-run this launcher." -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Reload user+machine PATH so the fresh install is visible
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:PATH    = "$machinePath;$userPath"

    # Re-check all candidate locations
    $candidates = @(
        "$env:LOCALAPPDATA\astral-sh\uv\bin\uv.exe"
        "$env:USERPROFILE\.local\bin\uv.exe"
        "$env:LOCALAPPDATA\uv\bin\uv.exe"
        "$env:APPDATA\uv\bin\uv.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $env:PATH = (Split-Path $candidate) + ";$env:PATH"
            break
        }
    }

    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uvCmd) {
        Write-Host ""
        Write-Host "uv was installed but still not found in PATH." -ForegroundColor Red
        Write-Host "Close this window, reopen it, and run launch.bat again." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to close"
        exit 1
    }

    Write-Host ""
    Write-Host "uv installed successfully." -ForegroundColor Green
    Write-Host ""
}

# --- 3. Run the app ---

# OneDrive and network drives do not support hardlinks; force file copies instead.
$env:UV_LINK_MODE = "copy"

Write-Host "Starting Well Report Processor..." -ForegroundColor Green
Write-Host "(First launch downloads and caches all dependencies - this may take" -ForegroundColor Yellow
Write-Host " several minutes; subsequent launches are instant.)" -ForegroundColor Yellow
Write-Host ""

uv run app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The application exited with error code $LASTEXITCODE." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit $LASTEXITCODE
}
