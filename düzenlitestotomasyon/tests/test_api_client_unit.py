"""Unit tests for GitsecApiClient — HTTP mock, staging'e gitmez."""
import json
from unittest.mock import MagicMock, patch

import pytest

from utils.api_client import GitsecApiClient


def test_sign_in_sets_token(monkeypatch):
    client = GitsecApiClient(base_url="https://staging.api.gitsec.io")
    monkeypatch.setattr(
        "utils.auth.sign_in_for_token",
        lambda email, password, api_base_url=None, timeout=15: "token-abc",
    )
    token = client.sign_in("a@b.com", "secret")
    assert token == "token-abc"
    assert client.token == "token-abc"


def test_assert_success_valid_payload():
    payload = {"success": True, "data": {"list": []}}
    GitsecApiClient.assert_success(200, payload, "/api/x")


def test_assert_success_raises_on_error_status():
    with pytest.raises(AssertionError):
        GitsecApiClient.assert_success(500, {"success": False}, "/api/x")


def test_get_attaches_bearer_token():
    client = GitsecApiClient(base_url="https://staging.api.gitsec.io", token="tok")
    captured = {}

    def fake_request(method, path, body=None, *, auth=True, timeout=30):
        captured["auth"] = auth
        captured["path"] = path
        return 200, {"success": True, "data": {}}

    client._request = fake_request  # type: ignore[method-assign]
    status, payload = client.get("/api/workspaces/83")
    assert status == 200
    assert captured["path"] == "/api/workspaces/83"
    assert captured["auth"] is True
