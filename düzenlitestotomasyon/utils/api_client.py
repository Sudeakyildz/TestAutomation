import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


class GitsecApiClient:
    """Staging GitSecurity API istemcisi — Swagger: /swagger/GitSecurity.API/swagger.json"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("API_BASE_URL", "https://staging.api.gitsec.io")).rstrip("/")
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        auth: bool = True,
        timeout: int = 30,
    ) -> tuple[int, dict | list | str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8", errors="replace")

        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, raw

    def sign_in(self, email: str, password: str) -> str:
        from utils.auth import sign_in_for_token

        self.token = sign_in_for_token(email, password, api_base_url=self.base_url)
        return self.token

    def get(self, path: str, *, auth: bool = True) -> tuple[int, Any]:
        return self._request("GET", path, auth=auth)

    def post(self, path: str, body: Any = None, *, auth: bool = True) -> tuple[int, Any]:
        return self._request("POST", path, body, auth=auth)

    def put(self, path: str, body: Any = None, *, auth: bool = True) -> tuple[int, Any]:
        return self._request("PUT", path, body, auth=auth)

    def patch(self, path: str, body: Any = None, *, auth: bool = True) -> tuple[int, Any]:
        return self._request("PATCH", path, body, auth=auth)

    def delete(self, path: str, body: Any = None, *, auth: bool = True) -> tuple[int, Any]:
        return self._request("DELETE", path, body, auth=auth)

    @staticmethod
    def assert_success(status: int, payload: Any, endpoint: str) -> None:
        assert status == 200, f"{endpoint} returned HTTP {status}: {payload}"
        if isinstance(payload, dict) and "success" in payload:
            assert payload["success"] is True, f"{endpoint} success=false: {payload}"
