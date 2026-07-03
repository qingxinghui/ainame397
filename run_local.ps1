$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = "F:\Anaconda3\envs\fastapi-env\python.exe"
if (-not (Test-Path $Python)) { throw "未找到 Python 环境：$Python" }

Write-Host "正在启动本机基础服务..." -ForegroundColor Cyan
docker compose up -d db postgres_db redis rabbitmq
if ($LASTEXITCODE -ne 0) { throw "Docker 基础服务启动失败" }

Write-Host "正在执行数据库迁移..." -ForegroundColor Cyan
& $Python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "MySQL 迁移失败" }

Write-Host "正在初始化 LangGraph 记忆表..." -ForegroundColor Cyan
& $Python init_pg_memory.py
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL 初始化失败" }

Write-Host "本机前端：http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "本机文档：http://127.0.0.1:8000/docs" -ForegroundColor Green
& $Python -m uvicorn main:app --reload
