Set-Location $PSScriptRoot\..
python scripts/preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest tests/ -m "regression and not write and not exploratory" --headless -v --tb=short --junitxml=reports/junit_regression.xml
