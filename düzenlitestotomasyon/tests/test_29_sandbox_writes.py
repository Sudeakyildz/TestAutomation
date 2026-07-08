"""
29. SANDBOX WRITE TEST
Gerçek POST/PUT/DELETE hamleleri — geçici kaynak oluşturulur ve temizlenir.
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import (
    create_backup_schedule,
    create_user_invite,
    delete_backup_schedule,
    delete_user_invite,
    get_first_repository,
    list_items,
    unique_name,
)
from tests.sandbox import SandboxWorkspace, create_sandbox_workspace, destroy_sandbox_workspace
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")

pytestmark = [pytest.mark.regression, pytest.mark.api, pytest.mark.write]


@pytest.fixture
def sandbox_workspace(api_client):
    ws_id, status, payload = create_sandbox_workspace(api_client)
    if not ws_id:
        pytest.skip(f"Sandbox workspace create not available: {status}")
    yield ws_id
    destroy_sandbox_workspace(api_client, ws_id)


def test_sandbox_workspace_update_and_verify(api_client, sandbox_workspace):
    """Sandbox workspace adını günceller ve doğrular."""
    new_name = unique_name("sandbox-upd")
    status, payload = api_client.put(
        f"/api/workspaces/{sandbox_workspace}",
        {"name": new_name, "description": "updated by e2e"},
    )
    assert status in (200, 204), f"Update failed: {status} {payload}"

    get_status, get_payload = api_client.get(f"/api/workspaces/{sandbox_workspace}")
    assert get_status == 200
    name = get_payload.get("data", {}).get("name", "")
    assert new_name in name or name == new_name


def test_sandbox_backup_schedule_create_and_delete(api_client, workspace_id):
    """Backup schedule oluşturur, doğrular, siler."""
    schedule_id, status, payload = create_backup_schedule(api_client, workspace_id)
    if not schedule_id:
        pytest.skip(f"Schedule create not available: {status} {payload}")

    get_status, _ = api_client.get(f"/api/backup/schedules/{schedule_id}")
    assert get_status == 200, f"Created schedule not readable: {get_status}"

    del_status, _ = delete_backup_schedule(api_client, schedule_id)
    assert del_status in (200, 204, 404), f"Schedule delete failed: {del_status}"
    logger.info("INFO: test step - Schedule %s created and deleted", schedule_id)


def test_sandbox_user_invite_create_and_delete(api_client, workspace_id):
    """Geçici davet oluşturur ve iptal eder."""
    invite_id, status, payload = create_user_invite(api_client, workspace_id)
    if not invite_id:
        pytest.skip(f"Invite create not allowed: {status} {payload}")

    del_status, _ = delete_user_invite(api_client, invite_id)
    assert del_status in (200, 204, 404), f"Invite delete failed: {del_status}"


def test_sandbox_update_profile_roundtrip(api_client):
    """Profil alanını okuyup aynı değerle UpdateProfile gönderir."""
    status, payload = api_client.get("/User/GetProfile")
    GitsecApiClient.assert_success(status, payload, "/User/GetProfile")
    profile = payload["data"]

    update_body = {
        "name": profile.get("name") or profile.get("firstName") or "Test",
        "surname": profile.get("surname") or profile.get("lastName") or "User",
        "companyName": profile.get("companyName") or "",
    }
    upd_status, upd_payload = api_client.post("/User/UpdateProfile", update_body)
    assert upd_status in (200, 400, 422), f"UpdateProfile failed: {upd_status} {upd_payload}"
    if upd_status == 200:
        GitsecApiClient.assert_success(upd_status, upd_payload, "/User/UpdateProfile")


def test_sandbox_license_inclusion_status_by_repo(api_client):
    """License inclusion listesinden ilk repo durumunu okur."""
    repo_id, _, _ = get_first_repository(api_client)
    if not repo_id:
        pytest.skip("No repository available.")
    status, payload = api_client.get("/api/repositories/license-inclusion-status")
    assert status in (200, 422), f"Unexpected status: {status}"
    if status != 200:
        return
    items = list_items(payload)
    repo_ids = {
        str(item.get("repositoryId") or item.get("id") or item.get("repoId"))
        for item in items
        if isinstance(item, dict)
    }
    assert str(repo_id) in repo_ids or not repo_ids, (
        f"Repo {repo_id} not found in license inclusion list"
    )


def test_sandbox_context_manager(api_client):
    """SandboxWorkspace context manager create/destroy."""
    try:
        with SandboxWorkspace(api_client) as ws_id:
            assert ws_id
            get_status, _ = api_client.get(f"/api/workspaces/{ws_id}")
            assert get_status == 200
    except RuntimeError as exc:
        pytest.skip(str(exc))
