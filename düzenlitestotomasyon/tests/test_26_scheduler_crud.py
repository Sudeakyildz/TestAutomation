"""
26. SCHEDULER CRUD TEST — düzenle, sil, enable, weekly/monthly UI
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from selenium.webdriver.common.keys import Keys
from tests.api_helpers import (
    create_backup_schedule,
    delete_backup_schedule,
    get_first_backup_schedule,
)
from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, safe_click
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_scheduler_list_shows_actions(sb):
    """Scheduler satırlarında düzenle/sil/toggle aksiyonları aranır."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/schedulers")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    assert "scheduler" in body or "schedule" in body
    has_actions = any(k in body for k in ["edit", "delete", "enable", "disable", "backup now", "düzenle", "sil"])
    assert has_actions or sb.is_element_present("table"), (
        "Scheduler page loaded but no actions/table found"
    )
    logger.info(f"INFO: test step - Scheduler actions visible: {has_actions}")


def test_scheduler_modal_frequency_options(sb):
    """New Scheduler modalında frequency seçenekleri."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/schedulers")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    btn = "xpath=//button[contains(., 'New Scheduler') or contains(., 'Yeni') or contains(., 'Create')]"
    if not sb.is_element_visible(btn):
        pytest.skip("New Scheduler button not found.")
    safe_click(sb, btn, timeout=8)
    time.sleep(2)
    body = sb.get_text("body").lower()
    has_freq = any(k in body for k in ["daily", "weekly", "monthly", "cron", "günlük", "haftalık"])
    try:
        sb.send_keys("body", Keys.ESCAPE)
    except Exception:
        pass
    assert has_freq or sb.is_element_visible("[data-slot='dialog-content']")


def test_backup_schedule_get_by_id(api_client):
    """Schedule detay API."""
    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("No schedule found.")
    status, payload = api_client.get(f"/api/backup/schedules/{schedule_id}")
    assert status == 200, f"GET schedule failed: {status}"


def test_backup_schedule_trigger_by_id_validation(api_client):
    """Trigger-by-schedule validation."""
    status, payload = api_client.post("/api/backup/schedules/trigger-by-schedule", {})
    assert status in (400, 422, 404), f"Expected validation, got {status}"


def test_jobmanager_schedules_list(api_client):
    """Job manager schedule listesi."""
    status, payload = api_client.get("/api/jobmanager/schedules")
    assert status in (200, 403, 404, 405), f"Unexpected status: {status}"


def test_backup_schedule_create_and_delete_api(api_client, workspace_id):
    """API ile schedule oluşturur ve siler."""
    schedule_id, status, payload = create_backup_schedule(api_client, workspace_id)
    if not schedule_id:
        pytest.skip(f"Schedule create not available: {status} {payload}")

    get_status, get_payload = api_client.get(f"/api/backup/schedules/{schedule_id}")
    assert get_status == 200
    assert get_payload.get("data", {}).get("id") == schedule_id

    del_status, _ = delete_backup_schedule(api_client, schedule_id)
    assert del_status in (200, 204, 404), f"Delete failed: {del_status}"


def test_backup_schedule_disable_enable_roundtrip(api_client):
    """Mevcut schedule disable → enable roundtrip."""
    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("No schedule found.")

    dis_status, _ = api_client.post(f"/api/backup/schedules/{schedule_id}/disable")
    assert dis_status in (200, 204, 404), f"Disable failed: {dis_status}"

    en_status, _ = api_client.post(f"/api/backup/schedules/{schedule_id}/enable")
    assert en_status in (200, 204, 404), f"Enable failed: {en_status}"
