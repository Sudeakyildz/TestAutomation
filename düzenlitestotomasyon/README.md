# GitSec Test Otomasyon

Staging ortamında GitSec için **API + E2E + sandbox write** test paketi.

## Hızlı başlangıç

```powershell
cd düzenlitestotomasyon
copy .env.example .env
# .env dosyasını doldurun

pip install -r requirements.txt
node server.js
```

Panel: http://localhost:3050

## Ortam değişkenleri

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `E2E_USER_EMAIL` | Evet | GitSec test hesabı |
| `E2E_USER_PASSWORD` | Evet | Şifre |
| `WORKSPACE_ID` | Evet | Dashboard workspace ID |
| `DASHBOARD_BASE_URL` | Hayır | Varsayılan: staging dashboard |
| `API_BASE_URL` | Hayır | Varsayılan: staging API |
| `GITHUB_TEST_USER` | Hayır | GitHub E2E (test_4–7) |
| `E2E_INVITE_ROLE_ID` | Hayır | Davet rolü (varsayılan: 4) |

## Test paketleri (pytest marker)

| Marker | Amaç | Süre |
|--------|------|------|
| `smoke` | API smoke + login + dashboard nav | ~5–10 dk |
| `regression` | Tam regresyon | ~1–2 saat |
| `write` | Gerçek POST/PUT/DELETE + cleanup | ~1 dk |
| `exploratory` | Gevşek API keşif testleri | Değişken |
| `unit` | Helper unit testleri | <10 sn |

### CLI

```powershell
python -m pytest tests/ -m smoke --headless -v
python -m pytest tests/ -m "regression and not write and not exploratory" --headless -v
python -m pytest tests/ -m write -v
python scripts/preflight.py
.\scripts\run_smoke.ps1
```

## Preflight

Her staging koşusundan önce: env + API sign-in + workspace erişimi.

Atlamak için: `--skip-preflight` veya `GITSEC_SKIP_PREFLIGHT=1`

## Bilinen GitSec bug'ları

- `test_5` Include/Exclude — xfail
- `test_7` Restore overlay — xfail

## Panel v2.5

Smoke / Regression / Write marker koşuları, kalıcı sonuçlar, maskelenmiş `.env`.

## CI secrets (GitHub Actions)

Repo: `Sudeakyildz/TestAutomation` — workflow: `.github/workflows/gitsec-e2e.yml`

### Otomatik ekleme

```powershell
gh auth login
cd düzenlitestotomasyon
.\scripts\setup_github_secrets.ps1
# GitHub test creds dahil:
.\scripts\setup_github_secrets.ps1 -IncludeOptional
```

Script yerel `.env` dosyanızı okur; şifreleri ekrana yazmaz, doğrudan GitHub Secrets'a gönderir.

### Manuel ekleme

GitHub → Settings → Secrets and variables → Actions → **New repository secret**

| Secret | Zorunlu |
|--------|---------|
| `E2E_USER_EMAIL` | Evet |
| `E2E_USER_PASSWORD` | Evet |
| `WORKSPACE_ID` | Evet |
| `DASHBOARD_BASE_URL` | Hayır |
| `API_BASE_URL` | Hayır |
| `GITHUB_TEST_USER` | Hayır |
| `GITHUB_TEST_PASSWORD` | Hayır |

