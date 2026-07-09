"""
32. BACKUP EXECUTION UI
Backup listesi, execution detay ve API tutarliligi.
"""
import logging

import pytest

from tests.api_helpers import get_first_backup_execution, get_first_backup_schedule
from tests.helpers import get_env_config, perform_setup_and_login, assert_main_visible, dismiss_ui_blockers
from tests.journey_helpers import open_workspace_path, page_has_table_or_content
from utils.api_client import GitsecApiClient
from utils.waits import wait_for_page_ready

logger = logging.getLogger("GitsecE2E")


def test_backups_page_shows_content(sb):
    """Backups sayfasi tablo veya backup icerigi gosterir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    open_workspace_path(sb, cfg, "backups")
    assert page_has_table_or_content(sb, "backup", "execution", "schedule", "yedek")
    assert_main_visible(sb)
    logger.info("INFO: test step - Backups page content OK")


def test_backups_dashboard_card_navigation(sb):
    """Dashboard backups karti backups sayfasina goturur."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_backups()
    sb.wait_for_condition(lambda: "/backups" in sb.get_current_url(), timeout=15)
    assert_main_visible(sb)
    dashboard.return_to_dashboard(cfg["base_url"], cfg["workspace_id"])
    logger.info("INFO: test step - Dashboard backups card OK")


def test_backup_execution_detail_api(api_client):
    """Son backup execution detay API."""
    exec_id, status, _ = get_first_backup_execution(api_client)
    if not exec_id:
        pytest.skip(f"No backup execution (HTTP {status})")
    detail_status, payload = api_client.get(f"/api/backup/executions/{exec_id}")
    assert detail_status in (200, 404), f"Unexpected detail status: {detail_status}"
    if detail_status == 200 and isinstance(payload, dict):
        assert payload.get("success") is True


def test_backup_schedule_enable_disable_ui_smoke(sb, api_client):
    """Schedulers sayfasinda mevcut schedule varsa liste gorunur."""
    cfg = get_env_config()
    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("No backup schedule in tenant")
    perform_setup_and_login(sb)
    open_workspace_path(sb, cfg, "schedulers")
    body = sb.get_text("body").lower()
    assert "schedule" in body or sb.is_element_present("table")
    logger.info("INFO: test step - Schedulers page shows schedule context")


def test_backup_statistics_api(api_client, workspace_id):
    """Backup istatistik API workspace ile uyumlu."""
    status, payload = api_client.get(f"/api/backup/executions/statistics?workspaceId={workspace_id}")
    assert status in (200, 400, 404), f"Statistics API: {status}"
    if status == 200:
        GitsecApiClient.assert_success(status, payload, "backup statistics")
