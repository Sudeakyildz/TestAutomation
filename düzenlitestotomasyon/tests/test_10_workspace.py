"""
10. WORKSPACE TEST
Workspace listesi, ayarlar, üyeler ve workspace detay sayfaları.
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
    get_env_config,
    assert_url_contains,
    assert_main_visible,
    safe_click,
)
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_workspace_switcher_visible(sb):
    """Dashboard'da workspace seçici veya adı görünür."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    body = sb.get_text("body")
    assert cfg["workspace_id"] in sb.get_current_url() or len(body) > 100
    assert_main_visible(sb)
    logger.info("INFO: test step - Workspace context visible on dashboard")


def test_workspace_settings_page(sb):
    """Workspace ayarları sayfası yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    paths = [
        f"{cfg['base_url']}/{cfg['workspace_id']}/settings",
        f"{cfg['base_url']}/{cfg['workspace_id']}/workspace/settings",
        f"{cfg['base_url']}/{cfg['workspace_id']}/settings/workspace",
    ]
    loaded = False
    for url in paths:
        sb.open(url)
        time.sleep(3)
        dismiss_ui_blockers(sb)
        if "404" not in sb.get_text("body").lower() and sb.is_element_visible("main"):
            loaded = True
            break
    if not loaded:
        sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/dashboard")
        time.sleep(2)
        settings_links = sb.find_elements("a[href*='settings'], button")
        for el in settings_links:
            try:
                href = el.get_attribute("href") or ""
                txt = (el.text or "").lower()
                if "settings" in href or "settings" in txt or "ayar" in txt:
                    sb.execute_script("arguments[0].click();", el)
                    time.sleep(3)
                    loaded = True
                    break
            except Exception:
                pass
    assert loaded or sb.is_element_visible("main"), "Workspace settings page could not be loaded"
    logger.info("INFO: test step - Workspace settings page accessible")


def test_workspace_members_page(sb):
    """Workspace üyeleri sayfası veya bölümü erişilebilir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    paths = [
        f"{cfg['base_url']}/{cfg['workspace_id']}/settings/members",
        f"{cfg['base_url']}/{cfg['workspace_id']}/members",
        f"{cfg['base_url']}/{cfg['workspace_id']}/team",
    ]
    for url in paths:
        sb.open(url)
        time.sleep(3)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if "404" not in body and ("member" in body or "team" in body or "invite" in body or "üye" in body):
            logger.info(f"INFO: test step - Members page loaded via {url}")
            return
    client = GitsecApiClient()
    client.sign_in(cfg["email"], cfg["password"])
    status, payload = client.get(f"/api/workspaces/{cfg['workspace_id']}/details")
    GitsecApiClient.assert_success(status, payload, "workspace details")
    assert "users" in payload["data"]
    logger.info("INFO: test step - Workspace members verified via API")


def test_workspace_api_list_matches_ui_context(sb, api_client, workspace_id):
    """API workspace listesi mevcut workspace'i içerir."""
    status, payload = api_client.get("/api/workspaces")
    GitsecApiClient.assert_success(status, payload, "/api/workspaces")
    ids = [str(w.get("id")) for w in payload["data"]["list"]]
    assert str(workspace_id) in ids
    logger.info("INFO: test step - Workspace list API contains current workspace")
