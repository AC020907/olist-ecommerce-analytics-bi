# Rebuilds the PostgreSQL database the Power BI report imports from
# (localhost:5432/olist_analytics) and runs the data-quality gate.
# The password is read interactively and only lives in this process's environment.
#
#   powershell -ExecutionPolicy Bypass -File scripts/rebuild_powerbi_source.ps1
#
# DESTRUCTIVE for that database: drops and recreates the raw, staging, analytics and
# reporting schemas from data/raw (nothing else in the database is touched).
param(
    [string]$PgHost = "localhost",
    [int]$Port = 5432,
    [string]$User = "postgres",
    [string]$Database = "olist_analytics"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$secure = Read-Host "PostgreSQL password for $User@${PgHost}:$Port" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    $env:DATABASE_URL = "postgresql://$User@${PgHost}:$Port/$Database"
    Push-Location $repo
    & $python -m olist_bi build
    if ($LASTEXITCODE -ne 0) { throw "build failed" }
    & $python -m olist_bi check
    if ($LASTEXITCODE -ne 0) { throw "data-quality gate failed" }
    Write-Host "`nDone. In Power BI Desktop: Home > Refresh, then File > Save." -ForegroundColor Green
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
