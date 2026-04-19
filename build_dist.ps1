# build_dist.ps1
# Builds WellReportProcessor.exe with PyInstaller, then zips dist\WellReportProcessor\.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File build_dist.ps1

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$appName    = "WellReportProcessor"
$specFile   = Join-Path $projectRoot "$appName.spec"
$distDir    = Join-Path $projectRoot "dist\$appName"
$zipName    = "$appName.zip"
$zipPath    = Join-Path $projectRoot $zipName

# ── Verify PyInstaller is available ──────────────────────────────────────────

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "pyinstaller not found. Install it with:  pip install pyinstaller"
    exit 1
}

# ── Clean previous build artefacts ───────────────────────────────────────────

foreach ($dir in @("build", "dist")) {
    $p = Join-Path $projectRoot $dir
    if (Test-Path $p) {
        Write-Host "Removing $dir\ ..." -ForegroundColor DarkGray
        Remove-Item $p -Recurse -Force
    }
}

# ── Run PyInstaller ───────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Running PyInstaller ..." -ForegroundColor Cyan
pyinstaller $specFile --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller failed (exit code $LASTEXITCODE)."
    exit $LASTEXITCODE
}

# ── Add a results\ placeholder inside the dist folder ────────────────────────

$resultsDst = Join-Path $distDir "results"
if (-not (Test-Path $resultsDst)) {
    New-Item -ItemType Directory -Path $resultsDst | Out-Null
}
Set-Content (Join-Path $resultsDst ".keep") "" -Encoding ASCII
Write-Host "  + results\.keep (placeholder)"

# ── Zip the dist folder ───────────────────────────────────────────────────────
# Use .NET ZipFile instead of Compress-Archive — the latter fails with an
# "in use by another process" error on base_library.zip inside PyInstaller dist.

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host ""
Write-Host "Creating $zipName ..." -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($distDir, $zipPath,
    [System.IO.Compression.CompressionLevel]::Optimal, $false)

# ── Report ────────────────────────────────────────────────────────────────────

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host ""
Write-Host "Done: $zipPath  ($sizeMB MB)" -ForegroundColor Green
Write-Host "Executable: dist\$appName\$appName.exe" -ForegroundColor Green
Write-Host ""
Write-Host "Distribution instructions:" -ForegroundColor Cyan
Write-Host "  1. Send $zipName to the end user."
Write-Host "  2. User extracts the zip to any folder."
Write-Host "  3. User double-clicks launch.bat."
Write-Host "     - uv is installed automatically if missing (requires internet, one-time)."
Write-Host "     - All Python dependencies are downloaded and cached (one-time)."
Write-Host "     - The app opens."
