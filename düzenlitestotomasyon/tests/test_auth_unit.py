"""Unit tests for utils.auth — staging'e gitmez."""
import json
from unittest.mock import MagicMock, patch

import pytest

from utils.auth import clear_sign_in_token_cache, sign_in_for_token


@pytest.fixture(autouse=True)
def _reset_auth_cache():
    clear_sign_in_token_cache()
    yield
    clear_sign_in_token_cache()


def test_sign_in_for_token_success():
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps(
        {"success": True, "data": {"token": "jwt-123"}}
    ).encode("utf-8")
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=response):
        token = sign_in_for_token("user@test.com", "pass", api_base_url="https://api.example.com")
    assert token == "jwt-123"


def test_sign_in_for_token_missing_token_raises():
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps({"success": True, "data": {}}).encode("utf-8")
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=response):
        with pytest.raises(AssertionError, match="missing token"):
            sign_in_for_token("user@test.com", "pass", api_base_url="https://api.example.com")
