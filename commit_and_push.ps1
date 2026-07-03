$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "[1/3] Staging project changes..." -ForegroundColor Cyan
git add -A
if ($LASTEXITCODE -ne 0) { throw "git add failed" }

Write-Host "[2/3] Creating commit..." -ForegroundColor Cyan
git commit -m "feat: expand naming platform and deployment workflow"
if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

Write-Host "[3/3] Pushing main to GitHub..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed" }

Write-Host "Push completed." -ForegroundColor Green
git log -1 --oneline
