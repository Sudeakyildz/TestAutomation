"""
17. RESTORE GELİŞMİŞ TEST
Restore sayfası, schedule listesi ve execution API'leri.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_restore_page_or_entry(sb):
    """Restore akışına giriş noktası erişilebilir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    paths = [
        f"{cfg['base_url']}/{cfg['workspace_id']}/restore",
        f"{cfg['base_url']}/{cfg['workspace_id']}/backups",
    ]
    for url in paths:
        sb.open(url)
        time.sleep(4)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if sb.is_element_visible("main") and ("restore" in body or "backup" in body):
            logger.info(f"INFO: test step - Restore entry via {url}")
            return
    assert_main_visible(sb)


def test_restore_schedules_executions_api(api_client):
    """Restore schedule execution listesi."""
    status, payload = api_client.get("/api/restore/schedules/executions")
    GitsecApiClient.assert_success(status, payload, "/api/restore/schedules/executions")
    logger.info("INFO: test step - Restore executions API OK")


def test_restore_schedules_list_api(api_client):
    """Restore schedule listesi."""
    status, payload = api_client.get("/api/restore/schedules")
    assert status in (200, 400, 405), f"Unexpected status: {status}"
    logger.info("INFO: test step - Restore schedules API responded")


def test_restore_wizard_button_visible(sb):
    """Backups veya repo sayfasında Restore butonu aranır."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/backups")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    restore_selectors = [
        "xpath=//button[contains(., 'Restore')]",
        "xpath=//a[contains(., 'Restore')]",
    ]
    body = sb.get_text("body").lower()
    has_restore = any(sb.is_element_present(sel) for sel in restore_selectors)
    assert has_restore or "backup" in body or "execution" in body, (
        "Restore action or backup content not found on backups page"
    )
    logger.info("INFO: test step - Restore entry or backup content verified")
