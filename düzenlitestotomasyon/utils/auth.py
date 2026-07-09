"""Paylasilan staging API sign-in — login_page ve GitsecApiClient icin."""
import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional

SIGN_IN_MAX_ATTEMPTS = 6
TOKEN_CACHE_TTL_SECONDS = 3600
_TOKEN_CACHE: dict[tuple[str, str], tuple[str, float]] = {}


def _format_sign_in_error(status: int, raw: str) -> str:
    lowered = raw.lower()
    if status >= 500 and (
        "23503" in raw
        or "activity" in lowered
        or "quotaexceeded" in lowered
        or "throttler" in lowered
    ):
        return (
            f"SignIn HTTP {status}: staging gecici hata (rate-limit veya activity kaydi). "
            "Birkac dakika bekleyip tekrar deneyin."
        )
    if len(raw) > 240:
        raw = raw[:240] + "..."
    return f"SignIn failed with HTTP {status}: {raw}"


def clear_sign_in_token_cache() -> None:
    """Testler arasi veya unit testlerde cache temizligi."""
    _TOKEN_CACHE.clear()


def sign_in_for_token(
    email: str,
    password: str,
    *,
    api_base_url: Optional[str] = None,
    timeout: int = 15,
    use_cache: bool = True,
) -> str:
    """Staging API uzerinden bearer token dondurur."""
    base = (api_base_url or os.getenv("API_BASE_URL", "https://staging.api.gitsec.io")).rstrip("/")
    cache_key = (email.lower(), base)
    if use_cache:
        cached = _TOKEN_CACHE.get(cache_key)
        if cached and time.time() < cached[1]:
            return cached[0]
    url = f"{base}/Auth/SignIn"
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    raw = ""
    status = 0
    for attempt in range(SIGN_IN_MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            status = exc.code
            if status >= 500 and attempt < SIGN_IN_MAX_ATTEMPTS - 1:
                time.sleep(min(2 ** attempt, 32))
                continue
            raise AssertionError(_format_sign_in_error(status, raw)) from exc

        if status >= 500 and attempt < SIGN_IN_MAX_ATTEMPTS - 1:
            time.sleep(min(2 ** attempt, 32))
            continue
        if status != 200:
            raise AssertionError(_format_sign_in_error(status, raw))
        break
    else:
        raise AssertionError(_format_sign_in_error(status, raw) if status else "SignIn failed after retries")

    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise AssertionError(f"SignIn success=false: {payload}")

    token = payload.get("data", {}).get("token")
    if not token:
        raise AssertionError(f"SignIn response missing token: {payload}")
    if use_cache:
        _TOKEN_CACHE[cache_key] = (token, time.time() + TOKEN_CACHE_TTL_SECONDS)
    return token
