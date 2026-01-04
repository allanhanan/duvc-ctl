$ErrorActionPreference = 'SilentlyContinue'

$packageName = 'duvc-cli'
$chocolateyBin = Join-Path $env:ChocolateyInstall "bin"
$targetExe = Join-Path $chocolateyBin "duvc-cli.exe"

Write-Host "Uninstalling $packageName..." -ForegroundColor Cyan

if (Test-Path $targetExe) {
    Remove-Item $targetExe -Force
    Write-Host "✓ Removed: $targetExe" -ForegroundColor Green
}

Write-Host "✓ $packageName uninstalled" -ForegroundColor Green
