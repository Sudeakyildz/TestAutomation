"""Paylasilan staging API sign-in — login_page ve GitsecApiClient icin."""
import json
import os
import urllib.error
import urllib.request
from typing import Optional


def sign_in_for_token(
    email: str,
    password: str,
    *,
    api_base_url: Optional[str] = None,
    timeout: int = 15,
) -> str:
    """Staging API uzerinden bearer token dondurur."""
    base = (api_base_url or os.getenv("API_BASE_URL", "https://staging.api.gitsec.io")).rstrip("/")
    url = f"{base}/Auth/SignIn"
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"SignIn failed with HTTP {exc.code}: {raw}") from exc

    if status != 200:
        raise AssertionError(f"SignIn failed with HTTP {status}: {raw}")

    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise AssertionError(f"SignIn success=false: {payload}")

    token = payload.get("data", {}).get("token")
    if not token:
        raise AssertionError(f"SignIn response missing token: {payload}")
    return token
