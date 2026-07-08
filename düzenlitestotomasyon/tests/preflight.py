"""Staging ortam preflight — test koşusundan once API ve env dogrulama."""
import os

from utils.api_client import GitsecApiClient


REQUIRED_ENV = (
    "E2E_USER_EMAIL",
    "E2E_USER_PASSWORD",
    "WORKSPACE_ID",
)


def _ascii_safe(value):
    text = str(value)
    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "backslashreplace").decode("ascii")


def validate_env():
    """Zorunlu env degiskenlerini kontrol eder."""
    errors = []
    for key in REQUIRED_ENV:
        if not os.getenv(key):
            errors.append(f"Missing environment variable: {key}")
    return errors


def validate_api_access():
    """Staging API sign-in ve workspace erisimini dogrular."""
    errors = []
    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    workspace_id = os.getenv("WORKSPACE_ID")

    try:
        client = GitsecApiClient()
        client.sign_in(email, password)
    except Exception as exc:
        errors.append(f"API sign-in failed: {_ascii_safe(exc)}")
        return errors

    status, payload = client.get(f"/api/workspaces/{workspace_id}")
    if status != 200:
        errors.append(f"Workspace {workspace_id} not accessible: HTTP {status}")

    status, payload = client.get("/api/repositories/tenant")
    if status != 200:
        errors.append(f"Repository list unavailable: HTTP {status}")

    return errors


def run_preflight():
    """Tum preflight kontrollerini calistirir."""
    errors = validate_env()
    if errors:
        return errors
    return validate_api_access()
