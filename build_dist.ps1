# build_dist.ps1
# Creates WellReportProcessor.zip in the project root.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File build_dist.ps1

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$zipName    = "WellReportProcessor.zip"
$zipPath    = Join-Path $projectRoot $zipName
$stagingDir = Join-Path $projectRoot "_dist_staging"

# ── Source files to include ───────────────────────────────────────────────────

$sourceFiles = @(
    "app.py"
    "process_report.py"
    "reg_expressions.py"
    "paths.py"
    "settings.py"
    "rag.py"
    "main.py"
    "pyproject.toml"
    "uv.lock"
    "well_test_data_paths.json"
    "launch.bat"
    "launch.ps1"
    "README.md"
)

# ── Clean up any previous staging area ───────────────────────────────────────

if (Test-Path $stagingDir) {
    Remove-Item $stagingDir -Recurse -Force
}
New-Item -ItemType Directory -Path $stagingDir | Out-Null

# ── Copy source files ─────────────────────────────────────────────────────────

# Files that must be ASCII to survive all unzip tools on any locale
$asciiFiles = @("launch.ps1", "launch.bat")

foreach ($file in $sourceFiles) {
    $src = Join-Path $projectRoot $file
    if (Test-Path $src) {
        $dst = Join-Path $stagingDir $file
        if ($asciiFiles -contains $file) {
            # Re-encode as ASCII (strips BOM, replaces non-ASCII with ?)
            $content = Get-Content $src -Raw -Encoding UTF8
            [System.IO.File]::WriteAllText($dst, $content, [System.Text.Encoding]::ASCII)
        } else {
            Copy-Item $src $dst
        }
        Write-Host "  + $file"
    } else {
        Write-Host "  ~ skipped (not found): $file" -ForegroundColor DarkGray
    }
}

# ── Copy static/ examples (PDFs only — skip cached JSON results) ─────────────

$staticSrc = Join-Path $projectRoot "static"
if (Test-Path $staticSrc) {
    $staticDst = Join-Path $stagingDir "static"
    New-Item -ItemType Directory -Path $staticDst | Out-Null
    Get-ChildItem $staticSrc -File | Where-Object { $_.Extension -match "^\.(pdf|PDF)$" } | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $staticDst $_.Name)
        Write-Host "  + static\$($_.Name)"
    }
}

# ── Create empty results/ directory (placeholder) ────────────────────────────

$resultsDst = Join-Path $stagingDir "results"
New-Item -ItemType Directory -Path $resultsDst | Out-Null
# Add a hidden placeholder so the folder is preserved in the zip
Set-Content (Join-Path $resultsDst ".keep") "" -Encoding ASCII
Write-Host "  + results\.keep (placeholder)"

# ── Build the zip ─────────────────────────────────────────────────────────────

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host ""
Write-Host "Creating $zipName ..." -ForegroundColor Cyan

Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal

# ── Clean up staging area ─────────────────────────────────────────────────────

Remove-Item $stagingDir -Recurse -Force

# ── Report ────────────────────────────────────────────────────────────────────

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host ""
Write-Host "Done: $zipPath  ($sizeMB MB)" -ForegroundColor Green
Write-Host ""
Write-Host "Distribution instructions:" -ForegroundColor Cyan
Write-Host "  1. Send $zipName to the end user."
Write-Host "  2. User extracts the zip to any folder."
Write-Host "  3. User double-clicks launch.bat."
Write-Host "     - uv is installed automatically if missing (requires internet, one-time)."
Write-Host "     - All Python dependencies are downloaded and cached (one-time)."
Write-Host "     - The app opens."
