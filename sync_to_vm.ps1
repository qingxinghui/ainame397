$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Remote = "qingxinghui@192.168.137.128"
$RemoteProject = "~/ainame397"
$Archive = Join-Path $env:TEMP "ainame397-code.tar.gz"

$Directories = @(
    "alembictable", "core", "frontend", "models", "repository",
    "routers", "schemas", "services", "settings", "tests"
)
$Files = @(
    "main.py", "dependencies.py", "requirements.txt", "Dockerfile",
    "docker-compose.yml", "nginx.conf", "alembic.ini",
    "init_pg_memory.py", "company_rules.txt", "test_main.http"
)

Write-Host "[1/4] Packing project code (excluding .env and data)..." -ForegroundColor Cyan
Push-Location $ProjectRoot
try {
    if (Test-Path $Archive) { Remove-Item $Archive -Force }
    & tar -czf $Archive @Directories @Files
    if ($LASTEXITCODE -ne 0) { throw "Failed to create archive" }
}
finally {
    Pop-Location
}

Write-Host "[2/4] Uploading code to the virtual machine..." -ForegroundColor Cyan
& scp $Archive "${Remote}:/tmp/ainame397-code.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "Upload failed" }

Write-Host "[3/4] Building images and running migrations..." -ForegroundColor Cyan
$RemoteCommand = @"
set -e
cd $RemoteProject
tar -xzf /tmp/ainame397-code.tar.gz
rm -f /tmp/ainame397-code.tar.gz
DOCKER_BUILDKIT=0 docker compose build web rag_worker
docker compose run --rm web alembic upgrade head </dev/null
docker compose up -d --force-recreate web rag_worker nginx
sleep 12
docker compose ps
curl -fsS -o /dev/null -w 'home=%{http_code}\n' http://127.0.0.1/
curl -fsS -o /dev/null -w 'docs=%{http_code}\n' http://127.0.0.1/docs
"@
& ssh $Remote $RemoteCommand
if ($LASTEXITCODE -ne 0) { throw "Remote deployment failed" }

Write-Host "[4/4] Sync completed: http://192.168.137.128" -ForegroundColor Green
Remove-Item $Archive -Force -ErrorAction SilentlyContinue
