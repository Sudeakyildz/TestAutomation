"""
0. STAGING API TEST
Swagger kaynağı: https://staging.api.gitsec.io/swagger/index.html
OpenAPI spec: /swagger/GitSecurity.API/swagger.json

Staging API uç noktalarının erişilebilirliğini ve temel yanıt yapısını doğrular.
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.api_client import GitsecApiClient
from tests.api_helpers import (
    BACKUP_DASHBOARD_RECENT_PATH,
    get_user_profile,
    extract_user_email,
)


class TestAuthApi:
    def test_signin_returns_token(self):
        email = os.getenv("E2E_USER_EMAIL")
        password = os.getenv("E2E_USER_PASSWORD")
        client = GitsecApiClient()
        token = client.sign_in(email, password)
        assert isinstance(token, str) and len(token) > 20

    def test_signin_rejects_invalid_credentials(self):
        client = GitsecApiClient()
        status, payload = client.post(
            "/Auth/SignIn",
            {"email": "invalid@test.local", "password": "wrong-password-123"},
            auth=False,
        )
        assert status in (400, 401, 403, 422), f"Expected auth failure, got {status}: {payload}"


class TestUserApi:
    def test_get_profile(self, api_client):
        status, payload = get_user_profile(api_client)
        GitsecApiClient.assert_success(status, payload, "user profile")
        assert extract_user_email(payload)

    def test_get_session(self, api_client):
        status, payload = api_client.get("/User/GetSession")
        GitsecApiClient.assert_success(status, payload, "/User/GetSession")
        assert payload["data"]["sessionUser"]["userId"]


class TestWorkspaceApi:
    def test_list_workspaces(self, api_client):
        status, payload = api_client.get("/api/workspaces")
        GitsecApiClient.assert_success(status, payload, "/api/workspaces")
        assert payload["data"]["list"]

    def test_get_workspace(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/workspaces/{workspace_id}")
        GitsecApiClient.assert_success(status, payload, f"/api/workspaces/{workspace_id}")
        assert str(payload["data"]["id"]) == str(workspace_id)

    def test_get_workspace_details(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/workspaces/{workspace_id}/details")
        GitsecApiClient.assert_success(status, payload, f"/api/workspaces/{workspace_id}/details")
        assert "users" in payload["data"]


class TestRepositoryApi:
    def test_list_tenant_repositories(self, api_client):
        status, payload = api_client.get("/api/repositories/tenant")
        GitsecApiClient.assert_success(status, payload, "/api/repositories/tenant")
        assert "list" in payload["data"]

    def test_list_repositories(self, api_client):
        status, payload = api_client.get("/api/repositories")
        GitsecApiClient.assert_success(status, payload, "/api/repositories")
        assert "data" in payload


class TestBackupApi:
    def test_dashboard_recent_executions(self, api_client):
        status, payload = api_client.get("/api/backup/executions/dashboard-recent")
        GitsecApiClient.assert_success(status, payload, "/api/backup/executions/dashboard-recent")
        assert "recentAll" in payload["data"]

    def test_recent_executions(self, api_client):
        status, payload = api_client.get(BACKUP_DASHBOARD_RECENT_PATH)
        GitsecApiClient.assert_success(status, payload, BACKUP_DASHBOARD_RECENT_PATH)
        data = payload["data"]
        assert any(key in data for key in ("recentAll", "recentActive", "recentCompleted", "list"))

    def test_backup_statistics(self, api_client):
        status, payload = api_client.get("/api/backup/executions/statistics")
        GitsecApiClient.assert_success(status, payload, "/api/backup/executions/statistics")

    def test_backup_schedules_tenant(self, api_client):
        status, payload = api_client.get("/api/backup/schedules/tenant")
        GitsecApiClient.assert_success(status, payload, "/api/backup/schedules/tenant")
        assert "list" in payload["data"]

    def test_backup_success_rate(self, api_client):
        status, payload = api_client.get("/api/backup/executions/backup-success-rate")
        GitsecApiClient.assert_success(status, payload, "/api/backup/executions/backup-success-rate")


class TestLicenceApi:
    def test_current_licence(self, api_client):
        status, payload = api_client.get("/api/licences/current")
        GitsecApiClient.assert_success(status, payload, "/api/licences/current")
        assert payload["data"]["status"]

    def test_usage_summary(self, api_client):
        status, payload = api_client.get("/api/licences/usage-summary")
        GitsecApiClient.assert_success(status, payload, "/api/licences/usage-summary")

    def test_licence_plans(self, api_client):
        status, payload = api_client.get("/api/licence-mapping/plans")
        GitsecApiClient.assert_success(status, payload, "/api/licence-mapping/plans")


class TestActivityApi:
    def test_activities_enums(self, api_client):
        status, payload = api_client.get("/api/activities/enums")
        GitsecApiClient.assert_success(status, payload, "/api/activities/enums")

    def test_workspace_activities(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/activities/workspace/{workspace_id}")
        GitsecApiClient.assert_success(status, payload, f"/api/activities/workspace/{workspace_id}")
        assert "list" in payload["data"]

    def test_user_activities(self, api_client):
        status, payload = api_client.get("/api/activities/user")
        GitsecApiClient.assert_success(status, payload, "/api/activities/user")


class TestStorageApi:
    def test_tenant_storage_providers(self, api_client):
        status, payload = api_client.get("/api/storage-providers/tenant")
        assert status == 200, f"/api/storage-providers/tenant returned {status}: {payload}"
        assert "list" in payload

    def test_global_storage_providers(self, api_client):
        status, payload = api_client.get("/api/storage-providers/global")
        GitsecApiClient.assert_success(status, payload, "/api/storage-providers/global")


class TestRestoreApi:
    def test_restore_schedules_executions(self, api_client):
        status, payload = api_client.get("/api/restore/schedules/executions")
        GitsecApiClient.assert_success(status, payload, "/api/restore/schedules/executions")


class TestInstallationsApi:
    def test_list_installations(self, api_client):
        status, payload = api_client.get("/api/installations")
        GitsecApiClient.assert_success(status, payload, "/api/installations")


class TestWorkspaceMembershipApi:
    def test_workspace_users(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/workspace-memberships/workspaces/{workspace_id}/users")
        assert status in (200, 404), f"Unexpected status: {status}"


class TestLicenceExtendedApi:
    def test_remaining_limits(self, api_client):
        status, payload = api_client.get("/api/licences/remaining-limits")
        assert status in (200, 404, 422), f"Unexpected status: {status}"

    def test_credit_history(self, api_client):
        status, payload = api_client.get("/api/licences/credit-history")
        assert status in (200, 404), f"Unexpected status: {status}"
