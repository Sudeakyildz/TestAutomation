"""
34. ACTIVITY JOURNEY
Activity sayfasi, dashboard linkleri ve API.
"""
import logging

import pytest

from tests.helpers import get_env_config, perform_setup_and_login, assert_main_visible
from tests.journey_helpers import open_workspace_path, page_has_table_or_content
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_activity_page_loads(sb):
    """Activity sayfasi yuklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    open_workspace_path(sb, cfg, "activity")
    assert page_has_table_or_content(sb, "activity", "task", "execution", "completed", "aktivite")
    assert_main_visible(sb)


def test_activity_from_dashboard_view_all(sb):
    """Dashboard Active Tasks / Recently Completed activity'ye gider."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_active_tasks_view_all()
    sb.wait_for_condition(
        lambda: "/activity" in sb.get_current_url() or "/schedulers" in sb.get_current_url(),
        timeout=15,
    )
    assert_main_visible(sb)


def test_activity_workspace_api(api_client, workspace_id):
    """Workspace activity API."""
    status, payload = api_client.get(f"/api/activity/workspace/{workspace_id}")
    assert status in (200, 400, 404), f"Activity API: {status}"
    if status == 200:
        GitsecApiClient.assert_success(status, payload, "activity workspace")


def test_activity_enums_api(api_client):
    """Activity enum API."""
    status, payload = api_client.get("/api/activity/enums")
    assert status in (200, 404), f"Enums API: {status}"
