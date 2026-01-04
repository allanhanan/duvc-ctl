$ErrorActionPreference = 'Stop'

$packageName = 'duvc-cli'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Installing $packageName..." -ForegroundColor Cyan

# Select architecture-specific binary
$exeName = if ([Environment]::Is64BitOperatingSystem) {
    "duvc-cli-x64.exe"
} else {
    "duvc-cli-x86.exe"
}

$sourceExe = Join-Path $toolsDir $exeName

if (-not (Test-Path $sourceExe)) {
    throw "Binary not found: $sourceExe"
}

# Copy to Chocolatey bin (automatically in PATH)
$chocolateyBin = Join-Path $env:ChocolateyInstall "bin"
$targetExe = Join-Path $chocolateyBin "duvc-cli.exe"

Copy-Item $sourceExe $targetExe -Force

Write-Host "Successfully installed $packageName" -ForegroundColor Green
Write-Host "Run duvc-cli --help to get started" -ForegroundColor Yellow
