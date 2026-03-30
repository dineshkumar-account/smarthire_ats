Set-Location $PSScriptRoot\smarthire_ats_frontend
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
python run.py
