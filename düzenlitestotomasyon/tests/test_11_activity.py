"""
11. ACTIVITY & BİLDİRİM TEST
Activity sayfası, filtreler ve bildirim alanı.
"""
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from tests.journey_helpers import open_workspace_path, page_has_table_or_content
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_activity_page_loads(sb):
    """Activity sayfası yüklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    open_workspace_path(sb, cfg, "activity")
    assert page_has_table_or_content(sb, "activity", "task", "execution", "completed", "aktivite", "backup")
    assert_main_visible(sb)
    logger.info("INFO: test step - Activity page loaded")


def test_activity_from_dashboard_links(sb):
    """Dashboard Active Tasks / Recently Completed linkleri activity sayfasına gider."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_active_tasks_view_all()
    sb.wait_for_condition(
        lambda: "activity" in sb.get_current_url() or "scheduler" in sb.get_current_url(),
        timeout=15,
    )
    assert_main_visible(sb)
    dashboard.return_to_dashboard(cfg["base_url"], cfg["workspace_id"])
    dashboard.navigate_to_recently_completed_view_all()
    sb.wait_for_condition(lambda: "activity" in sb.get_current_url(), timeout=15)
    assert_main_visible(sb)
    logger.info("INFO: test step - Dashboard activity links work")


def test_activity_api_workspace(sb, api_client, workspace_id):
    """Workspace activity API yanıt verir."""
    status, payload = api_client.get(f"/api/activities/workspace/{workspace_id}")
    GitsecApiClient.assert_success(status, payload, f"/api/activities/workspace/{workspace_id}")
    assert "list" in payload["data"]
    logger.info("INFO: test step - Workspace activities API OK")


def test_activity_api_user(api_client):
    """Kullanıcı activity API yanıt verir."""
    status, payload = api_client.get("/api/activities/user")
    GitsecApiClient.assert_success(status, payload, "/api/activities/user")
    logger.info("INFO: test step - User activities API OK")


def test_activity_api_enums(api_client):
    """Activity enum listesi döner."""
    status, payload = api_client.get("/api/activities/enums")
    GitsecApiClient.assert_success(status, payload, "/api/activities/enums")
    logger.info("INFO: test step - Activity enums API OK")


def test_activity_category_counts(api_client, workspace_id):
    """Activity kategori sayıları API."""
    status, payload = api_client.get(f"/api/activities/category-counts?workspaceId={workspace_id}")
    if status == 200:
        logger.info("INFO: test step - Activity category counts API OK")
    else:
        status2, payload2 = api_client.get("/api/activities/category-counts")
        assert status2 in (200, 400, 422), f"Unexpected status: {status2}"
