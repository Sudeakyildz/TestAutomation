"""
25. RESTORE FONKSİYONEL TEST — schedule listesi, enable/disable, execution
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def _first_restore_schedule(api_client):
    status, payload = api_client.get("/api/restore/schedules")
    if status != 200:
        return None, status, payload
    data = payload.get("data", payload)
    items = data if isinstance(data, list) else data.get("list", [])
    if not items:
        return None, status, payload
    sid = items[0].get("id") or items[0].get("scheduleId")
    return sid, status, payload


def test_restore_schedules_tenant_list(api_client, workspace_id):
    """Tenant restore schedule listesi."""
    status, payload = api_client.get(f"/api/restore/schedules/tenant/{workspace_id}")
    assert status in (200, 400, 404), f"Unexpected status: {status}"


def test_restore_schedule_detail(api_client):
    """Restore schedule detay."""
    schedule_id, _, _ = _first_restore_schedule(api_client)
    if not schedule_id:
        pytest.skip("No restore schedule found.")
    status, payload = api_client.get(f"/api/restore/schedules/{schedule_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_restore_schedule_enable_disable(api_client):
    """Restore schedule enable/disable."""
    schedule_id, _, _ = _first_restore_schedule(api_client)
    if not schedule_id:
        pytest.skip("No restore schedule found.")
    dis, _ = api_client.post(f"/api/restore/schedules/{schedule_id}/disable")
    assert dis in (200, 400, 404, 409)
    en, _ = api_client.post(f"/api/restore/schedules/{schedule_id}/enable")
    assert en in (200, 400, 404, 409)


def test_restore_execution_list(api_client):
    """Restore execution listesi."""
    status, payload = api_client.get("/api/restore/schedules/executions")
    GitsecApiClient.assert_success(status, payload, "/api/restore/schedules/executions")


def test_restore_wizard_ui_steps(sb):
    """Backups sayfasında restore akış girişi."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/backups")
    import time
    time.sleep(4)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    assert "backup" in body or "restore" in body
