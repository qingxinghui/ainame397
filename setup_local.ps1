$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = "F:\Anaconda3\envs\fastapi-env\python.exe"
if (-not (Test-Path $Python)) { throw "未找到 Python 环境：$Python" }

Write-Host "正在安装 Python 依赖..." -ForegroundColor Cyan
& $Python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if ($LASTEXITCODE -ne 0) { throw "依赖安装失败" }

Write-Host "本机环境准备完成，请运行 .\run_local.ps1" -ForegroundColor Green
