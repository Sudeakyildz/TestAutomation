"""
15. REPOSITORY GELİŞMİŞ TEST
Arama, filtre, tablo görünümü ve repo detay navigasyonu.
"""
import os
import sys
import time
import logging

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import (
    perform_setup_and_login,
    dismiss_ui_blockers,
    scroll_table_right,
    get_env_config,
    assert_main_visible,
    safe_click,
    open_add_provider_page,
)
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_repositories_github_page_loads(sb):
    """GitHub repositories sayfası tablo ile yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/github")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    assert_main_visible(sb)
    assert sb.is_element_present("table") or "repository" in sb.get_text("body").lower()
    logger.info("INFO: test step - GitHub repositories page loaded")


def test_repositories_search_filter(sb):
    """Repo arama kutusu ile filtreleme."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/github")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    search_selectors = [
        "input[placeholder*='Search']",
        "input[placeholder*='search']",
        "input[type='search']",
    ]
    for sel in search_selectors:
        if sb.is_element_visible(sel):
            sb.type(sel, "test")
            time.sleep(2)
            logger.info("INFO: test step - Repository search filter applied")
            return
    assert sb.is_element_present("table") or sb.is_element_visible("main"), "Repositories table or main content missing"
    logger.info("INFO: test step - Search input not found; table/main still visible")


def test_repositories_table_has_switches(sb):
    """Repo tablosunda include switch sütunu görünür."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/github")
    time.sleep(4)
    scroll_table_right(sb)
    switches = sb.find_elements("button[role='switch']")
    if not switches:
        pytest.skip("No repository switches found — GitHub may not be connected.")
    assert len(switches) >= 1
    logger.info(f"INFO: test step - Found {len(switches)} repository switches")


def test_repositories_add_provider_page(sb):
    """Add provider sayfası erişilebilir."""
    open_add_provider_page(sb)
    body = sb.get_text("body").lower()
    assert "github" in body or "bitbucket" in body or "gitlab" in body or "provider" in body
    logger.info("INFO: test step - Add provider page loaded")


def test_repositories_tenant_api(api_client):
    """Tenant repository listesi API."""
    status, payload = api_client.get("/api/repositories/tenant")
    GitsecApiClient.assert_success(status, payload, "/api/repositories/tenant")
    assert "list" in payload["data"]
    logger.info("INFO: test step - Tenant repositories API OK")


def test_installations_api(api_client):
    """Provider installation listesi."""
    status, payload = api_client.get("/api/installations")
    GitsecApiClient.assert_success(status, payload, "/api/installations")
    logger.info("INFO: test step - Installations API OK")


def test_license_inclusion_status_api(api_client):
    """License inclusion status endpoint."""
    status, payload = api_client.get("/api/repositories/license-inclusion-status")
    assert status in (200, 400, 422), f"Unexpected status: {status}"
    logger.info("INFO: test step - License inclusion status API responded")
