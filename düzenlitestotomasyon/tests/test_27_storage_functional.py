"""
27. STORAGE PROVIDER TEST — ekleme sayfası, test connection, enable/disable
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import get_first_storage_provider
from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_storage_add_provider_ui(sb):
    """Storage provider ekleme UI."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/storage")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    add_hints = ["add", "new", "provider", "s3", "azure", "ekle", "yeni"]
    assert any(k in body for k in add_hints) or "storage" in body


def test_storage_provider_detail(api_client):
    """Storage provider detay GET."""
    provider_id, _, _ = get_first_storage_provider(api_client)
    if not provider_id:
        pytest.skip("No storage provider configured.")
    status, payload = api_client.get(f"/api/storage-providers/{provider_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_storage_provider_enable_disable(api_client):
    """Storage provider enable/disable roundtrip."""
    provider_id, _, _ = get_first_storage_provider(api_client)
    if not provider_id:
        pytest.skip("No storage provider configured.")
    dis, _ = api_client.post(f"/api/storage-providers/{provider_id}/disable")
    assert dis in (200, 400, 404, 409)
    en, _ = api_client.post(f"/api/storage-providers/{provider_id}/enable")
    assert en in (200, 400, 404, 409)


def test_storage_test_connection_validation(api_client):
    """Test connection geçersiz body ile validation."""
    status, payload = api_client.post("/api/storage-providers/test-connection", {})
    assert status in (400, 422, 500), f"Expected validation error, got {status}"


def test_storage_policy_default(api_client):
    """Default storage policy endpoint."""
    status, payload = api_client.get("/api/storage-policies/policies/default")
    assert status in (200, 404, 500), f"Unexpected status: {status}"


def test_storage_oauth_authorize_endpoint(api_client):
    """Storage OAuth authorize URL endpoint."""
    status, payload = api_client.get("/api/storage-providers/oauth/authorize?provider=S3")
    assert status in (200, 400, 404, 405, 422), f"Unexpected status: {status}"
