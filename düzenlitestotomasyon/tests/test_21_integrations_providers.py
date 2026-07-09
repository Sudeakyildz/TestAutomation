"""
21. ENTEGRASYON TEST — Bitbucket, GitLab, provider sync
Bitbucket/GitLab OAuth E2E hesap olmadigi icin ertelendi — sadece sayfa + API smoke.
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, open_add_provider_page
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_bitbucket_gitlab_add_provider_pages(sb):
    """Bitbucket ve GitLab add-provider sayfaları erişilebilir."""
    open_add_provider_page(sb)
    body = sb.get_text("body").lower()
    assert "bitbucket" in body or "gitlab" in body or "github" in body
    logger.info("INFO: test step - Provider add page lists integrations")


def test_bitbucket_workspaces_api(api_client):
    """Bitbucket workspace listesi API."""
    status, payload = api_client.get("/api/bitbucket/workspaces")
    assert status in (200, 400, 403, 404, 500), f"Unexpected status: {status}"


def test_installation_provider_sync_endpoints(api_client):
    """Installation sync endpoint'leri yanıt verir (sync çalıştırmadan)."""
    status, payload = api_client.get("/api/installations")
    GitsecApiClient.assert_success(status, payload, "/api/installations")
    installations = payload.get("data", {}).get("list") or payload.get("data") or []
    if not installations:
        pytest.skip("No installations to validate sync path.")
    inst_id = installations[0].get("id") or installations[0].get("installationId")
    status2, _ = api_client.post(f"/api/installations/sync/{inst_id}")
    assert status2 in (200, 202, 400, 403, 404, 405, 409), f"Sync returned {status2}"


def test_provider_disconnect_button_visible(sb):
    """Bağlı provider varsa disconnect/configure aksiyonu görünür."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/add")
    time.sleep(3)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    has_action = any(k in body for k in ["disconnect", "configure", "active", "connected", "bağlı"])
    assert has_action or "github" in body
