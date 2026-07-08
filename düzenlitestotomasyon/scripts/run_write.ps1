Set-Location $PSScriptRoot\..
python scripts/preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest tests/ -m write -v --tb=short --junitxml=reports/junit_write.xml
