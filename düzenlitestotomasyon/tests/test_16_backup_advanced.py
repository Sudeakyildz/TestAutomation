"""
16. BACKUP GELİŞMİŞ TEST
Backup listesi, istatistikler ve execution detayları.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_backups_page_loads(sb):
    """Backups sayfası yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/backups")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    assert_main_visible(sb)
    body = sb.get_text("body").lower()
    assert "backup" in body or "execution" in body or "schedule" in body
    logger.info("INFO: test step - Backups page loaded")


def test_backups_from_dashboard(sb):
    """Dashboard backups kartı."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_backups()
    assert "/backups" in sb.get_current_url()
    logger.info("INFO: test step - Backups card navigation OK")


def test_backup_executions_tenant_api(api_client):
    """Tenant backup execution listesi."""
    status, payload = api_client.get("/api/backup/executions/tenant")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/tenant")
    assert "list" in payload["data"]
    logger.info("INFO: test step - Backup executions tenant API OK")


def test_backup_statistics_api(api_client):
    """Backup istatistikleri."""
    status, payload = api_client.get("/api/backup/executions/statistics")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/statistics")
    logger.info("INFO: test step - Backup statistics API OK")


def test_backup_success_rate_api(api_client):
    """Backup başarı oranı."""
    status, payload = api_client.get("/api/backup/executions/backup-success-rate")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/backup-success-rate")
    logger.info("INFO: test step - Backup success rate API OK")


def test_backup_recent_executions_api(api_client):
    """Son backup execution'ları."""
    status, payload = api_client.get("/api/backup/executions/recent-executions")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/recent-executions")
    assert "list" in payload["data"]
    logger.info("INFO: test step - Recent executions API OK")


def test_backup_dashboard_recent_api(api_client):
    """Dashboard recent backups widget API."""
    status, payload = api_client.get("/api/backup/executions/dashboard-recent")
    GitsecApiClient.assert_success(status, payload, "/api/backup/executions/dashboard-recent")
    assert "recentAll" in payload["data"]
    logger.info("INFO: test step - Dashboard recent backups API OK")


def test_backup_snapshots_list_api(api_client):
    """Backup snapshot listesi."""
    status, payload = api_client.get("/api/backup/snapshots")
    assert status in (200, 400), f"Unexpected status: {status}"
    logger.info("INFO: test step - Backup snapshots API responded")
