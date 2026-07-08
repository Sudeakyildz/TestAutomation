"""
12. STORAGE TEST
Depolama sayfası, provider listesi ve kullanım istatistikleri.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_storage_page_loads(sb):
    """Storage sayfası yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/storage")
    time.sleep(3)
    dismiss_ui_blockers(sb)
    assert_main_visible(sb)
    body = sb.get_text("body").lower()
    assert "storage" in body or "depolama" in body or "provider" in body or "gb" in body
    logger.info("INFO: test step - Storage page loaded")


def test_storage_from_dashboard_card(sb):
    """Dashboard storage kartı storage sayfasına gider."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_storage()
    assert "/storage" in sb.get_current_url()
    logger.info("INFO: test step - Storage card navigation OK")


def test_storage_providers_tenant_api(api_client):
    """Tenant storage provider listesi."""
    status, payload = api_client.get("/api/storage-providers/tenant")
    assert status == 200, f"tenant storage providers failed: {status}"
    assert "list" in payload
    logger.info("INFO: test step - Tenant storage providers API OK")


def test_storage_providers_global_api(api_client):
    """Global storage provider listesi."""
    status, payload = api_client.get("/api/storage-providers/global")
    GitsecApiClient.assert_success(status, payload, "/api/storage-providers/global")
    logger.info("INFO: test step - Global storage providers API OK")


def test_storage_policy_check_api(api_client):
    """Storage policy check endpoint."""
    status, payload = api_client.get("/api/storage-policies/policies/check")
    assert status in (200, 400, 404), f"Unexpected status {status}: {payload}"
    logger.info("INFO: test step - Storage policy check API responded")


def test_backup_storage_usage_api(api_client):
    """Backup storage kullanım istatistikleri."""
    status, payload = api_client.get("/api/backup/executions/backup-storage-usage")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/backup-storage-usage")
    logger.info("INFO: test step - Backup storage usage API OK")
