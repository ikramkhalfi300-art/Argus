# Simulates the CI pipeline locally.
# Usage: .\run_ci_locally.ps1
# Requires: Python 3.13+, Node 24+, and optionally a running PostgreSQL instance.

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$passed = 0
$failed = 0

function Run-Check {
    param($Name, $ScriptBlock)
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $ScriptBlock
        Write-Host "  PASS  $Name" -ForegroundColor Green
        $script:passed++
    } catch {
        Write-Host "  FAIL  $Name  -- $_" -ForegroundColor Red
        $script:failed++
    }
}

# Job 1: Smoke test
Run-Check "Smoke test (backend health + frontend build)" {
    & python $rootDir\tests\smoke_test.py
    if ($LASTEXITCODE -ne 0) { throw "Smoke test failed with exit code $LASTEXITCODE" }
}

# Job 2: Backend DB tests against SQLite
Run-Check "DB tests (SQLite)" {
    $env:DATABASE_URL = ""
    & python -m pytest $rootDir\tests\test_db_operations.py $rootDir\tests\test_migration.py -v --tb=short
    if ($LASTEXITCODE -ne 0) { throw "SQLite DB tests failed" }
}

# Job 3: Backend DB tests against PostgreSQL (if available)
$pgUrl = $env:DATABASE_URL
if (-not $pgUrl) {
    # Check if PostgreSQL is running locally
    $pgAvailable = $false
    try {
        $listener = [System.Net.Sockets.TcpClient]::new()
        $listener.ConnectAsync("127.0.0.1", 5432).Wait(2000)
        if ($listener.Connected) {
            $listener.Close()
            $pgAvailable = $true
        }
    } catch { $pgAvailable = $false }

    if ($pgAvailable) {
        $pgUrl = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
    }
}

if ($pgUrl) {
    Run-Check "DB tests (PostgreSQL)" {
        $env:DATABASE_URL = $pgUrl
        & python -m pytest $rootDir\tests\test_db_operations.py $rootDir\tests\test_migration.py -v --tb=short
        if ($LASTEXITCODE -ne 0) { throw "PostgreSQL DB tests failed" }
    }
} else {
    Write-Host "`n=== DB tests (PostgreSQL) SKIPPED ===" -ForegroundColor Yellow
    Write-Host "  No PostgreSQL instance detected at localhost:5432." -ForegroundColor Yellow
    Write-Host "  The CI pipeline (GitHub Actions) provisions a Postgres service container automatically." -ForegroundColor Yellow
    Write-Host "  To run locally, start PostgreSQL and set: `$env:DATABASE_URL = 'postgresql+asyncpg://user:pass@host:5432/dbname'" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Results: $passed passed, $failed failed out of $($passed + $failed)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
exit $failed
