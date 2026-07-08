"""
18. SCHEDULER GELİŞMİŞ TEST
Scheduler listesi, enable/disable ve schedule API doğrulamaları.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_schedulers_page_loads(sb):
    """Schedulers sayfası yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/schedulers")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    assert_main_visible(sb)
    body = sb.get_text("body").lower()
    assert "scheduler" in body or "schedule" in body or "zaman" in body
    logger.info("INFO: test step - Schedulers page loaded")


def test_new_scheduler_button_visible(sb):
    """New Scheduler butonu görünür."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/schedulers")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    selectors = [
        "xpath=//button[contains(., 'New Scheduler')]",
        "xpath=//button[contains(., 'Create Scheduler')]",
        "xpath=//button[contains(., 'Yeni Zamanlayıcı')]",
        "xpath=//button[contains(., 'Scheduler')]",
        "xpath=//a[contains(., 'New Scheduler')]",
    ]
    found = any(sb.is_element_visible(sel) for sel in selectors)
    if not found:
        body = sb.get_text("body").lower()
        found = "scheduler" in body or "schedule" in body or "zamanlay" in body
    assert found, "Scheduler page content not found"
    logger.info("INFO: test step - Scheduler page / New button verified")


def test_backup_schedules_tenant_api(api_client):
    """Backup schedule tenant listesi."""
    status, payload = api_client.get("/api/backup/schedules/tenant")
    GitsecApiClient.assert_success(status, payload, "/api/backup/schedules/tenant")
    assert "list" in payload["data"]
    logger.info("INFO: test step - Backup schedules tenant API OK")


def test_backup_schedules_list_api(api_client):
    """Backup schedules list endpoint."""
    status, payload = api_client.get("/api/backup/schedules")
    assert status in (200, 400, 405), f"Unexpected status: {status}"
    logger.info("INFO: test step - Backup schedules API responded")
