"""API testleri için ortak yardımcılar."""
import logging
import os
import time
import uuid

logger = logging.getLogger("GitsecE2E")

DEFAULT_INVITE_ROLE_ID = int(os.getenv("E2E_INVITE_ROLE_ID", "4"))
USER_PROFILE_LEGACY_PATH = "/User/GetProfile"
USER_SESSION_PATH = "/User/GetSession"
BACKUP_RECENT_EXECUTIONS_PATH = "/api/backup/executions/recent-executions"
BACKUP_DASHBOARD_RECENT_PATH = "/api/backup/executions/dashboard-recent"


def extract_id(payload, *keys):
    """API yanıtından id alanını çıkarır."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data", payload)
    if isinstance(data, dict):
        for key in keys:
            val = data.get(key)
            if val is not None and val != 0:
                return val
    return None


def first_list_item(payload, list_keys=("list", "items", "data")):
    """API yanıtından ilk liste öğesini döndürür."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data", payload)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        for key in list_keys:
            items = data.get(key)
            if isinstance(items, list) and items:
                return items[0]
    return None


def list_items(payload, list_keys=("list", "items")):
    """API yanıtından liste döndürür."""
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", payload)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in list_keys:
            items = data.get(key)
            if isinstance(items, list):
                return items
    return []


def get_user_profile(api_client):
    """Kullanici profili — GetProfile kaldirildiysa GetSession fallback."""
    status, payload = api_client.get(USER_PROFILE_LEGACY_PATH)
    if status == 200:
        return status, payload

    status, payload = api_client.get(USER_SESSION_PATH)
    if status != 200 or not isinstance(payload, dict):
        return status, payload

    session_user = (payload.get("data") or {}).get("sessionUser")
    if not session_user:
        return status, payload

    return status, {
        "success": True,
        "data": session_user,
        "_source": USER_SESSION_PATH,
    }


def extract_user_email(profile_payload):
    """Profil veya session yanitindan e-posta cikarir."""
    if not isinstance(profile_payload, dict):
        return None
    data = profile_payload.get("data", profile_payload)
    if isinstance(data, dict):
        if data.get("email"):
            return data["email"]
        session_user = data.get("sessionUser")
        if isinstance(session_user, dict) and session_user.get("email"):
            return session_user["email"]
    return None


def get_backup_schedule_detail(api_client, schedule_id):
    """Schedule detayi — GET /schedules/{id} 405 ise tenant listesinden coz."""
    status, payload = api_client.get(f"/api/backup/schedules/{schedule_id}")
    if status == 200:
        return status, payload

    list_status, list_payload = api_client.get("/api/backup/schedules/tenant")
    if list_status != 200:
        return status, payload

    for item in list_items(list_payload):
        sid = item.get("id") or item.get("scheduleId")
        if str(sid) == str(schedule_id):
            return 200, {"success": True, "data": item, "_source": "tenant-list"}

    return status, payload


def _first_execution_from_payload(payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        return None

    for key in ("list", "recentAll", "recentActive", "recentCompleted", "items"):
        items = data.get(key)
        if isinstance(items, list) and items:
            item = items[0]
            if isinstance(item, dict):
                return item.get("id") or item.get("executionId")
    return None


def get_first_repository(api_client):
    status, payload = api_client.get("/api/repositories/tenant")
    if status != 200:
        return None, status, payload
    item = first_list_item(payload)
    if not item:
        return None, status, payload
    repo_id = item.get("id") or item.get("repositoryId")
    return repo_id, status, payload


def get_included_repository_id(api_client, workspace_id=None):
    """
    Schedule oluşturmak için license dahil repo ID döndürür.
    Önce mevcut schedule, sonra tenant listesi denenir.
    """
    status, payload = api_client.get("/api/backup/schedules/tenant")
    if status == 200:
        for item in list_items(payload):
            if not isinstance(item, dict):
                continue
            repo_id = item.get("repositoryId")
            if repo_id:
                return int(repo_id)

    status, payload = api_client.get("/api/repositories/tenant")
    if status == 200:
        for item in list_items(payload):
            if not isinstance(item, dict):
                continue
            repo_id = item.get("id") or item.get("repositoryId")
            included = item.get("isIncluded")
            if included is None:
                included = item.get("licenseInclusionStatus") in (1, True, "Included")
            if repo_id and included:
                return int(repo_id)

    repo_id, _, _ = get_first_repository(api_client)
    return int(repo_id) if repo_id else None


def get_first_backup_schedule(api_client):
    status, payload = api_client.get("/api/backup/schedules/tenant")
    if status != 200:
        return None, status, payload
    item = first_list_item(payload)
    if not item:
        return None, status, payload
    schedule_id = item.get("id") or item.get("scheduleId")
    return schedule_id, status, payload


def get_first_backup_execution(api_client):
    for path in (BACKUP_RECENT_EXECUTIONS_PATH, BACKUP_DASHBOARD_RECENT_PATH):
        status, payload = api_client.get(path)
        if status != 200:
            continue
        exec_id = _first_execution_from_payload(payload)
        if exec_id:
            return exec_id, status, payload
    return None, 404, {"message": "No backup execution found"}


def get_first_storage_provider(api_client):
    status, payload = api_client.get("/api/storage-providers/tenant")
    if status != 200:
        return None, status, payload
    data = payload if isinstance(payload, dict) else {}
    items = data.get("list") or data.get("data", {}).get("list") or []
    if not items:
        return None, status, payload
    return items[0].get("id"), status, payload


def unique_name(prefix="e2e-auto"):
    return f"{prefix}-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def build_backup_schedule_body(name, repository_id, workspace_id, cron_expression="0 30 3 * * ?"):
    """Staging API'nin kabul ettiği backup schedule body."""
    return {
        "name": name,
        "repositoryId": int(repository_id),
        "workspaceId": int(workspace_id),
        "triggerType": "Cron",
        "cronExpression": cron_expression,
        "scopes": [2, 3, 4],
        "isIncremental": False,
    }


def create_backup_schedule(api_client, workspace_id, repository_id=None, name=None):
    """
    Backup schedule oluşturur.
    Returns: (schedule_id, status, payload) — schedule_id None ise başarısız.
    """
    repo_id = repository_id or get_included_repository_id(api_client, workspace_id)
    if not repo_id:
        return None, 404, {"message": "No included repository available"}

    schedule_name = name or unique_name("e2e-sched")
    body = build_backup_schedule_body(schedule_name, repo_id, workspace_id)
    status, payload = api_client.post("/api/backup/schedules", body)
    if status not in (200, 201):
        return None, status, payload

    schedule_id = extract_id(payload, "scheduleId", "id")
    if not schedule_id:
        list_status, list_payload = api_client.get("/api/backup/schedules/tenant")
        if list_status == 200:
            for item in list_items(list_payload):
                if item.get("name") == schedule_name:
                    schedule_id = item.get("id") or item.get("scheduleId")
                    break

    return schedule_id, status, payload


def delete_backup_schedule(api_client, schedule_id):
    """Backup schedule siler."""
    if not schedule_id:
        return 404, {}
    return api_client.delete(f"/api/backup/schedules/{schedule_id}")


def find_user_invite_by_email(api_client, email):
    """Davet listesinden e-posta ile davet kaydı bulur."""
    status, payload = api_client.get("/api/user-invite/list-detail")
    if status != 200:
        return None, status, payload
    for item in list_items(payload):
        if isinstance(item, dict) and item.get("email") == email:
            return item.get("id") or item.get("userInviteId"), status, payload
    return None, status, payload


def create_user_invite(api_client, workspace_id, email=None, role_id=None):
    """
    Workspace daveti oluşturur.
    Returns: (invite_id, status, payload)
    """
    invite_email = email or f"e2e+sandbox+{uuid.uuid4().hex[:8]}@example.com"
    role = role_id if role_id is not None else DEFAULT_INVITE_ROLE_ID
    status, payload = api_client.post(
        "/api/user-invite/invite",
        {"email": invite_email, "workspaceId": int(workspace_id), "roleId": int(role)},
    )
    if status not in (200, 201):
        return None, status, payload

    invite_id = extract_id(payload, "id", "userInviteId", "inviteId")
    if not invite_id:
        invite_id, _, _ = find_user_invite_by_email(api_client, invite_email)

    return invite_id, status, payload


def delete_user_invite(api_client, invite_id):
    if not invite_id:
        return 404, {}
    return api_client.delete(f"/api/user-invite/{invite_id}")
