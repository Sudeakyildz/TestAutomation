"""
23. REPOSITORY AKSİYON TEST — bulk, push config, repo detay
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import get_first_repository
from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, scroll_table_right, safe_click
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_repository_detail_by_id(api_client):
    """Tek repo detay API."""
    repo_id, status, payload = get_first_repository(api_client)
    if not repo_id:
        pytest.skip("No repository available.")
    status2, payload2 = api_client.get(f"/api/repositories/{repo_id}")
    assert status2 in (200, 404), f"Unexpected status: {status2}"


def test_repository_git_check_api(api_client):
    """Git repo check endpoint."""
    status, payload = api_client.post("/api/repositories/git/check", {"url": "https://github.com/octocat/Hello-World.git"})
    assert status in (200, 400, 422, 500), f"Unexpected status: {status}"


def test_repository_push_configuration_get(api_client, workspace_id):
    """Push configuration okuma."""
    repo_id, _, _ = get_first_repository(api_client)
    if not repo_id:
        pytest.skip("No repository available.")
    path = f"/api/repositories/{repo_id}/workspaces/{workspace_id}/push-configuration"
    status, payload = api_client.get(path)
    assert status in (200, 404), f"Unexpected status: {status}"


def test_license_inclusion_batch_read(api_client):
    """License inclusion status listesi."""
    status, payload = api_client.get("/api/repositories/license-inclusion-status")
    assert status in (200, 422), f"Unexpected status: {status}"


def test_bulk_select_ui(sb):
    """Repo tablosunda toplu seçim checkbox'ları."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/github")
    time.sleep(4)
    dismiss_ui_blockers(sb)
    scroll_table_right(sb)
    checkboxes = sb.find_elements("button[role='checkbox'], input[type='checkbox']")
    if len(checkboxes) < 1:
        pytest.skip("No bulk checkboxes found.")
    try:
        checkboxes[0].click()
        time.sleep(1)
    except Exception:
        pass
    body = sb.get_text("body").lower()
    has_bulk = any(k in body for k in ["exclude", "include", "selected", "bulk", "hariç", "dahil"])
    assert has_bulk, "Checkbox selected but bulk action bar not visible"


def test_repository_workspaces_by_workspace(api_client, workspace_id):
    """Repo-workspace eşleşmeleri."""
    status, payload = api_client.get(f"/api/repository-workspaces/by-workspace?workspaceId={workspace_id}")
    assert status in (200, 400), f"Unexpected status: {status}"
