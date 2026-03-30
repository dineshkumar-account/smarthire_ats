Set-Location $PSScriptRoot\smarthire_ats_backend
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
