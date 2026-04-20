# E2E Test Runner for messagekit
# Tests complete event flow: EventBus → Outbox → Kafka → Consumer

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "E2E Test Runner - messagekit" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "[CHECK] Verifying Docker containers..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Docker Compose not available or not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker containers first:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d" -ForegroundColor White
    Write-Host ""
    exit 1
}

$requiredContainers = @("kafka", "postgres", "zookeeper")
$running = $containers -split "`n"

foreach ($container in $requiredContainers) {
    if ($running -notcontains $container) {
        Write-Host "❌ ERROR: Required container '$container' not running" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please start Docker containers:" -ForegroundColor Yellow
        Write-Host "  docker-compose up -d $container" -ForegroundColor White
        Write-Host ""
        exit 1
    }
}

Write-Host "✅ Docker containers running" -ForegroundColor Green
Write-Host ""

# Run E2E test
Write-Host "[RUN] Starting E2E test..." -ForegroundColor Yellow
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

Push-Location $projectRoot

try {
    # Run with Python
    python scripts/tests/e2e/run_e2e_test.py

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ E2E test completed successfully" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ E2E test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}
