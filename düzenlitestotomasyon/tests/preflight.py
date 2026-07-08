"""Staging ortam preflight — test koşusundan önce API ve env doğrulama."""
import os

from utils.api_client import GitsecApiClient


REQUIRED_ENV = (
    "E2E_USER_EMAIL",
    "E2E_USER_PASSWORD",
    "WORKSPACE_ID",
)


def validate_env():
    """Zorunlu env değişkenlerini kontrol eder."""
    errors = []
    for key in REQUIRED_ENV:
        if not os.getenv(key):
            errors.append(f"Eksik ortam değişkeni: {key}")
    return errors


def validate_api_access():
    """Staging API sign-in ve workspace erişimini doğrular."""
    errors = []
    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    workspace_id = os.getenv("WORKSPACE_ID")

    try:
        client = GitsecApiClient()
        client.sign_in(email, password)
    except Exception as exc:
        errors.append(f"API sign-in başarısız: {exc}")
        return errors

    status, payload = client.get(f"/api/workspaces/{workspace_id}")
    if status != 200:
        errors.append(f"Workspace {workspace_id} erişilemedi: HTTP {status}")

    status, payload = client.get("/api/repositories/tenant")
    if status != 200:
        errors.append(f"Repository listesi alınamadı: HTTP {status}")

    return errors


def run_preflight():
    """Tüm preflight kontrollerini çalıştırır."""
    errors = validate_env()
    if errors:
        return errors
    return validate_api_access()
