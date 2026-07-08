# GitHub Actions secrets — yerel .env dosyasından repo secret'larına aktarır.
# Önkoşul: gh CLI kurulu ve "gh auth login" yapılmış olmalı.
#
# Kullanım:
#   cd düzenlitestotomasyon
#   .\scripts\setup_github_secrets.ps1
#   .\scripts\setup_github_secrets.ps1 -IncludeOptional   # GitHub/AWS creds dahil

param(
    [switch]$IncludeOptional
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$RepoRoot = Split-Path $ProjectRoot -Parent
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    $RepoRoot = $ProjectRoot
}

$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env"
}
if (-not (Test-Path $EnvFile)) {
    Write-Error ".env bulunamadı: $EnvFile"
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    $ghExe = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $ghExe) {
        $env:Path += ";C:\Program Files\GitHub CLI"
    } else {
        Write-Error "GitHub CLI (gh) yüklü değil. Kurulum: winget install GitHub.cli"
    }
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "GitHub oturumu yok. Once su adimlari tamamlayin:" -ForegroundColor Yellow
    Write-Host "  1) gh auth login --hostname github.com --git-protocol https --web"
    Write-Host "  2) Cikan kodu https://github.com/login/device adresine girin"
    Write-Host "  3) Terminalde 'Authentication complete' gorunene kadar bekleyin"
    Write-Host "  4) Sonra tekrar: .\scripts\setup_github_secrets.ps1"
    Write-Host ""
    exit 1
}

function Read-EnvFile([string]$Path) {
    $vars = @{}
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        if ($val.StartsWith('"') -and $val.EndsWith('"')) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        $vars[$key] = $val
    }
    return $vars
}

$required = @(
    "E2E_USER_EMAIL",
    "E2E_USER_PASSWORD",
    "WORKSPACE_ID",
    "DASHBOARD_BASE_URL",
    "API_BASE_URL"
)

$optional = @(
    @{ Name = "E2E_GITHUB_TEST_USER"; Env = "GITHUB_TEST_USER" },
    @{ Name = "E2E_GITHUB_TEST_PASSWORD"; Env = "GITHUB_TEST_PASSWORD" },
    @{ Name = "E2E_GITHUB_MAIL_USER"; Env = "GITHUB_MAIL_USER" },
    @{ Name = "E2E_GITHUB_MAIL_PASSWORD"; Env = "GITHUB_MAIL_PASSWORD" },
    @{ Name = "E2E_INVITE_ROLE_ID"; Env = "E2E_INVITE_ROLE_ID" }
)

$envVars = Read-EnvFile $EnvFile
$toSet = @()
foreach ($name in $required) { $toSet += @{ Name = $name; Env = $name } }
if ($IncludeOptional) {
    $toSet += $optional
}

Set-Location $RepoRoot
Write-Host "Repo: $(gh repo view --json nameWithOwner -q .nameWithOwner)"
Write-Host "Kaynak: $EnvFile"
Write-Host ""

$ok = 0
$skip = 0
foreach ($item in $toSet) {
    $name = $item.Name
    $envKey = $item.Env
    if (-not $envVars.ContainsKey($envKey) -or [string]::IsNullOrWhiteSpace($envVars[$envKey])) {
        Write-Warning "Atlandı (boş/yok): $name"
        $skip++
        continue
    }
    $envVars[$envKey] | gh secret set $name
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK  $name"
        $ok++
    } else {
        Write-Error "Secret eklenemedi: $name"
    }
}

Write-Host ""
Write-Host "Tamamlandı: $ok secret eklendi, $skip atlandı."
Write-Host "GitHub -> Settings -> Secrets and variables -> Actions bölümünden doğrulayın."
