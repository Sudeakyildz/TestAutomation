"""
24. BACKUP FONKSİYONEL TEST — execution detay, snapshot, iptal, trigger
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import get_first_backup_execution, get_first_backup_schedule, get_first_repository
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_backup_execution_detail(api_client):
    """Backup execution detay GET."""
    exec_id, _, _ = get_first_backup_execution(api_client)
    if not exec_id:
        pytest.skip("No backup execution found.")
    status, payload = api_client.get(f"/api/backup/executions/{exec_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_backup_executions_by_repository(api_client):
    """Repo bazlı backup execution listesi."""
    repo_id, _, _ = get_first_repository(api_client)
    if not repo_id:
        pytest.skip("No repository available.")
    status, payload = api_client.get(f"/api/backup/executions/repository/{repo_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_backup_snapshots_by_execution(api_client):
    """Execution snapshot listesi."""
    exec_id, _, _ = get_first_backup_execution(api_client)
    if not exec_id:
        pytest.skip("No backup execution found.")
    status, payload = api_client.get(f"/api/backup/snapshots/{exec_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_backup_schedule_detail(api_client):
    """Backup schedule detay GET."""
    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("No backup schedule found.")
    status, payload = api_client.get(f"/api/backup/schedules/{schedule_id}")
    assert status in (200, 404), f"Unexpected status: {status}"


def test_backup_schedule_enable_disable_roundtrip(api_client):
    """Mevcut schedule enable/disable toggle (geri alınır)."""
    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("No backup schedule found.")

    dis_status, _ = api_client.post(f"/api/backup/schedules/{schedule_id}/disable")
    assert dis_status in (200, 400, 404, 409), f"Disable failed: {dis_status}"

    en_status, _ = api_client.post(f"/api/backup/schedules/{schedule_id}/enable")
    assert en_status in (200, 400, 404, 409), f"Enable failed: {en_status}"


def test_backup_trigger_rejects_empty_body(api_client):
    """Trigger endpoint boş body ile validation."""
    status, payload = api_client.post("/api/backup/schedules/trigger", {})
    assert status in (400, 422, 404), f"Expected validation error, got {status}"
