"""
20. KAPSAMLI API TEST
Swagger'daki ek read-only endpoint'ler — workspace, üyelik, invite, restore, enterprise.
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.api_client import GitsecApiClient


class TestWorkspaceMembershipApi:
    def test_workspace_users(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/workspace-memberships/workspaces/{workspace_id}/users")
        assert status in (200, 404), f"Unexpected status: {status}"
        if status == 200:
            assert "list" in payload.get("data", payload)

    def test_workspace_memberships_list(self, api_client):
        status, payload = api_client.get("/api/workspace-memberships")
        assert status in (200, 400, 405), f"Unexpected status: {status}"


class TestUserInviteApi:
    def test_invite_list_detail(self, api_client):
        status, payload = api_client.get("/api/user-invite/list-detail")
        assert status in (200, 400, 403), f"Unexpected status: {status}"


class TestRepositoryWorkspaceApi:
    def test_repository_workspaces_by_workspace(self, api_client, workspace_id):
        status, payload = api_client.get(f"/api/repository-workspaces/by-workspace?workspaceId={workspace_id}")
        assert status in (200, 400), f"Unexpected status: {status}"


class TestLicenceExtendedApi:
    def test_credit_history(self, api_client):
        status, payload = api_client.get("/api/licences/credit-history")
        assert status in (200, 404), f"Unexpected status: {status}"

    def test_downgrade_preview(self, api_client):
        status, payload = api_client.get("/api/licences/downgrade/preview")
        assert status in (200, 400, 405, 422), f"Unexpected status: {status}"

    def test_licence_features(self, api_client):
        status, payload = api_client.get("/api/licence-mapping/features")
        GitsecApiClient.assert_success(status, payload, "/api/licence-mapping/features")


class TestEnterpriseApi:
    def test_enterprise_packages(self, api_client):
        status, payload = api_client.get("/api/enterprise-packages")
        assert status in (200, 403, 404), f"Unexpected status: {status}"


class TestAuthExtendedApi:
    def test_authorization_claims_schema(self, api_client):
        status, payload = api_client.get("/Auth/GetAuthorizationClaimsSchema")
        assert status in (200, 403, 405), f"Unexpected status: {status}"

    def test_authorization_claims_of_user(self, api_client):
        status, payload = api_client.get("/Auth/GetAuthorizationClaimsOfUser")
        assert status in (200, 403, 405), f"Unexpected status: {status}"


class TestStoragePolicyApi:
    def test_default_storage_policy(self, api_client):
        status, payload = api_client.get("/api/storage-policies/policies/default")
        assert status in (200, 404, 500), f"Unexpected status: {status}"


class TestJobManagerApi:
    def test_jobmanager_schedules(self, api_client):
        status, payload = api_client.get("/api/jobmanager/schedules")
        assert status in (200, 403, 404, 405), f"Unexpected status: {status}"
