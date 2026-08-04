# Lean start after envs are fixed (ENVIRONMENT=demo in backend/.env, DEMO in frontend/.env).
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "Starting DBs..." -ForegroundColor Cyan
docker compose up -d postgres neo4j redis
Start-Sleep -Seconds 6

$py = Join-Path $Root "backend\.venv\Scripts\python.exe"
Push-Location (Join-Path $Root "backend")
& $py -m alembic upgrade head
& $py -m scripts.seed
Pop-Location

Push-Location (Join-Path $Root "frontend")
npm run build
Pop-Location

docker compose -f deploy/docker-compose.tunnel.yml up -d

Write-Host ""
Write-Host "Done. Now open TWO terminals and run only:" -ForegroundColor Green
Write-Host ""
Write-Host "  # API" -ForegroundColor Yellow
Write-Host "  cd $Root\backend"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  uvicorn app.main:app --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "  # Tunnel" -ForegroundColor Yellow
Write-Host "  cloudflared tunnel --url http://127.0.0.1:8080"
Write-Host ""
Write-Host "Sir login: supervisor.mumbai@maharashtracyber.gov.in / SecurePolice@2026" -ForegroundColor Cyan
