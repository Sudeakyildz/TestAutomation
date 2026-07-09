"""Staging ortam preflight — test koşusundan once API ve env dogrulama."""
import os
import time

from utils.api_client import GitsecApiClient


REQUIRED_ENV = (
    "E2E_USER_EMAIL",
    "E2E_USER_PASSWORD",
    "WORKSPACE_ID",
)

PREFLIGHT_API_ATTEMPTS = 5
PREFLIGHT_INITIAL_DELAY_SECONDS = 8


def _ascii_safe(value):
    text = str(value)
    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "backslashreplace").decode("ascii")


def format_preflight_error(message: str) -> str:
    """Uzun staging hata metinlerini panel/terminal icin kisaltir."""
    text = _ascii_safe(message)
    lowered = text.lower()
    if "signin http 500" in lowered and (
        "23503" in text
        or "activity" in lowered
        or "quotaexceeded" in lowered
        or "gecici hata" in lowered
    ):
        return (
            "API sign-in failed: staging gecici olarak yanit vermiyor "
            "(rate-limit / activity kaydi). Birkac dakika bekleyip tekrar deneyin "
            "veya panelden 'Preflight atla' secenegini kullanin."
        )
    if len(text) > 320:
        return text[:320] + "..."
    return text


def validate_env():
    """Zorunlu env degiskenlerini kontrol eder."""
    errors = []
    for key in REQUIRED_ENV:
        if not os.getenv(key):
            errors.append(f"Missing environment variable: {key}")
    return errors


def validate_api_access():
    """Staging API sign-in ve workspace erisimini dogrular."""
    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    workspace_id = os.getenv("WORKSPACE_ID")
    last_error = None

    if PREFLIGHT_INITIAL_DELAY_SECONDS > 0:
        time.sleep(PREFLIGHT_INITIAL_DELAY_SECONDS)

    for attempt in range(PREFLIGHT_API_ATTEMPTS):
        errors = []
        try:
            client = GitsecApiClient()
            client.sign_in(email, password)
        except Exception as exc:
            last_error = format_preflight_error(f"API sign-in failed: {exc}")
            if attempt < PREFLIGHT_API_ATTEMPTS - 1:
                time.sleep(min(10 * (attempt + 1), 45))
                continue
            return [last_error]

        status, _payload = client.get(f"/api/workspaces/{workspace_id}")
        if status != 200:
            errors.append(f"Workspace {workspace_id} not accessible: HTTP {status}")

        status, _payload = client.get("/api/repositories/tenant")
        if status != 200:
            errors.append(f"Repository list unavailable: HTTP {status}")

        if errors:
            last_error = format_preflight_error("; ".join(errors))
            if attempt < PREFLIGHT_API_ATTEMPTS - 1:
                time.sleep(min(5 * (attempt + 1), 20))
                continue
            return [format_preflight_error(err) for err in errors]

        return []

    return [last_error or "API preflight failed after retries"]


def run_preflight():
    """Tum preflight kontrollerini calistirir."""
    errors = validate_env()
    if errors:
        return [format_preflight_error(err) for err in errors]
    return validate_api_access()
