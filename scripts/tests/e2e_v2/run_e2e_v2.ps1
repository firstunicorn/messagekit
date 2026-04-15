# E2E V2 Test Runner - Separate Databases
# Real-world microservices scenario

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "E2E Test V2 - Separate Databases (Database-per-Service)" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

Push-Location $scriptDir

try {
    # Step 1: Start Docker containers
    Write-Host "[STEP 1] Starting Docker containers..." -ForegroundColor Yellow
    Write-Host "  • postgres-producer (port 5433)" -ForegroundColor White
    Write-Host "  • postgres-consumer (port 5434)" -ForegroundColor White
    Write-Host "  • kafka (port 9093)" -ForegroundColor White
    Write-Host "  • zookeeper (port 2182)" -ForegroundColor White
    Write-Host ""
    
    docker-compose -f docker-compose.e2e.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start Docker containers" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Docker containers started" -ForegroundColor Green
    Write-Host ""
    
    # Step 2: Wait for services to be healthy
    Write-Host "[STEP 2] Waiting for services to be healthy..." -ForegroundColor Yellow
    Write-Host "  Waiting 15 seconds for containers to initialize..." -ForegroundColor White
    Start-Sleep -Seconds 15
    
    # Check container status
    $containers = docker-compose -f docker-compose.e2e.yml ps --services --filter "status=running" 2>&1
    $running = $containers -split "`n"
    
    $required = @("postgres-producer", "postgres-consumer", "kafka", "zookeeper")
    $allRunning = $true
    
    foreach ($container in $required) {
        if ($running -contains $container) {
            Write-Host "  ✅ $container" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $container" -ForegroundColor Red
            $allRunning = $false
        }
    }
    
    if (-not $allRunning) {
        Write-Host ""
        Write-Host "❌ Some containers are not running" -ForegroundColor Red
        Write-Host "Check logs with: docker-compose -f docker-compose.e2e.yml logs" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ All containers healthy" -ForegroundColor Green
    Write-Host ""
    
    # Step 3: Run E2E test
    Write-Host "[STEP 3] Running E2E test..." -ForegroundColor Yellow
    Write-Host ""
    
    Push-Location $projectRoot
    
    & "$projectRoot\.venv\Scripts\python.exe" "$scriptDir\run_e2e_test_v2.py"
    
    $testExitCode = $LASTEXITCODE
    
    Pop-Location
    
    Write-Host ""
    
    if ($testExitCode -eq 0) {
        Write-Host "✅ E2E test completed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ E2E test failed with exit code: $testExitCode" -ForegroundColor Red
    }
    
    # Step 4: Cleanup option
    Write-Host ""
    Write-Host "[CLEANUP] Docker containers are still running." -ForegroundColor Yellow
    Write-Host "  To stop: docker-compose -f docker-compose.e2e.yml down" -ForegroundColor White
    Write-Host "  To stop and remove volumes: docker-compose -f docker-compose.e2e.yml down -v" -ForegroundColor White
    Write-Host ""
    
    exit $testExitCode
    
} finally {
    Pop-Location
}
