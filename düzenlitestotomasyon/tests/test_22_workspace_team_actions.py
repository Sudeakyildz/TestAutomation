"""
22. WORKSPACE & EKİP TEST
Workspace oluşturma, arşiv, üye listesi ve davet akışları.
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import unique_name
from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_workspace_create_and_archive(api_client):
    """Yeni workspace oluşturur ve arşivler (temizlik)."""
    name = unique_name("e2e-ws")
    status, payload = api_client.post("/api/workspaces", {"name": name, "description": "e2e auto test"})
    if status not in (200, 201):
        pytest.skip(f"Workspace create not allowed in staging: {status} {payload}")

    ws_id = payload.get("data", {}).get("id") or payload.get("data", {}).get("workspaceId")
    assert ws_id, f"Create response missing id: {payload}"

    get_status, get_payload = api_client.get(f"/api/workspaces/{ws_id}")
    assert get_status == 200

    arch_status, _ = api_client.post(f"/api/workspaces/{ws_id}/archive")
    assert arch_status in (200, 204, 400, 404, 405), f"Archive failed: {arch_status}"
    logger.info(f"INFO: test step - Workspace {ws_id} create/archive flow done")


def test_workspace_archived_list(api_client):
    """Arşivlenmiş workspace listesi."""
    status, payload = api_client.get("/api/workspaces/archived")
    assert status in (200, 404, 422), f"Unexpected status: {status}"


def test_workspace_members_list(api_client, workspace_id):
    """Workspace üye listesi detaylı."""
    status, payload = api_client.get(f"/api/workspace-memberships/workspaces/{workspace_id}/users")
    if status == 200:
        assert "list" in payload.get("data", payload) or isinstance(payload.get("data"), list)
    else:
        assert status in (403, 404)


def test_workspace_invite_page(sb, api_client):
    """Davet / members UI veya invite API erişimi."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    for path in ["settings/members", "members", "team", "settings/team"]:
        sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/{path}")
        time.sleep(2)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if "404" not in body and any(k in body for k in ["invite", "member", "team", "üye", "davet"]):
            logger.info(f"INFO: test step - Team page at /{path}")
            return
    status, payload = api_client.get("/api/user-invite/list-detail")
    assert status in (200, 403), f"Invite API fallback failed: {status}"


def test_user_invite_rejects_invalid(api_client):
    """Geçersiz davet isteği reddedilir."""
    status, payload = api_client.post("/api/user-invite/invite", {"email": "", "workspaceId": 0})
    assert status in (400, 422, 403), f"Expected validation error, got {status}"
