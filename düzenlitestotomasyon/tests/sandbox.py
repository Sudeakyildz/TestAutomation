"""Sandbox workspace — gerçek write testleri için oluştur/temizle."""
import logging

from tests.api_helpers import extract_id, unique_name

logger = logging.getLogger("GitsecE2E")


def create_sandbox_workspace(api_client, prefix="sandbox"):
    """Geçici workspace oluşturur. Başarısızsa None."""
    name = unique_name(prefix)
    status, payload = api_client.post(
        "/api/workspaces",
        {"name": name, "description": "E2E sandbox — otomatik silinir"},
    )
    if status not in (200, 201):
        logger.warning("Sandbox workspace create failed: %s %s", status, payload)
        return None, status, payload
    ws_id = extract_id(payload, "id", "workspaceId")
    return ws_id, status, payload


def destroy_sandbox_workspace(api_client, workspace_id):
    """Sandbox workspace'i arşivler veya siler."""
    if not workspace_id:
        return
    for method, path in [
        ("post", f"/api/workspaces/{workspace_id}/archive"),
        ("delete", f"/api/workspaces/{workspace_id}"),
    ]:
        try:
            if method == "post":
                status, _ = api_client.post(path)
            else:
                status, _ = api_client.delete(path)
            logger.info("Sandbox cleanup %s %s -> %s", method.upper(), path, status)
            if status in (200, 204, 404):
                return
        except Exception as exc:
            logger.warning("Sandbox cleanup error: %s", exc)


class SandboxWorkspace:
    """Context manager: sandbox workspace oluşturur, çıkışta temizler."""

    def __init__(self, api_client):
        self.api_client = api_client
        self.workspace_id = None

    def __enter__(self):
        self.workspace_id, status, payload = create_sandbox_workspace(self.api_client)
        if not self.workspace_id:
            raise RuntimeError(f"Sandbox workspace could not be created: {status} {payload}")
        return self.workspace_id

    def __exit__(self, exc_type, exc, tb):
        destroy_sandbox_workspace(self.api_client, self.workspace_id)
        return False
