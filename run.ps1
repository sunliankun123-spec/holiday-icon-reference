Set-Location $PSScriptRoot

$python = "$env:LocalAppData\Programs\Python\Python312\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  & $python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r app/requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8765
