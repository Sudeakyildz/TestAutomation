Set-Location $PSScriptRoot\..
python scripts/preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest tests/ -m smoke --headless -v --tb=short --junitxml=reports/junit_smoke.xml
