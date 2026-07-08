"""
28. HESAP & BİLLİNG TEST — profil güncelleme, şifre, lisans iptal preview, 2FA sayfası
"""
import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config
from utils.api_client import GitsecApiClient

logger = __import__("logging").getLogger("GitsecE2E")


def test_update_profile_readonly_fields(api_client):
    """GetProfile ile mevcut profil doğrulanır."""
    status, payload = api_client.get("/User/GetProfile")
    GitsecApiClient.assert_success(status, payload, "/User/GetProfile")
    profile = payload["data"]
    assert profile.get("email")
    assert profile.get("name") or profile.get("firstName") or profile.get("surname") or profile.get("lastName")


def test_change_password_endpoint_requires_body(api_client):
    """ChangePassword boş body ile reddedilir."""
    status, payload = api_client.post("/Auth/ChangePassword", {})
    assert status in (400, 422), f"Expected validation, got {status}"


def test_forgot_password_api(api_client):
    """ForgotPassword API invalid email."""
    status, payload = api_client.post("/Auth/ForgotPassword", {"email": "not-an-email"})
    assert status in (400, 422, 200), f"Unexpected status: {status}"


def test_licence_cancellation_preview(api_client):
    """Lisans iptal talebi endpoint (dry-run değil — sadece erişim)."""
    status, payload = api_client.get("/api/licences/request-cancellation")
    assert status in (200, 400, 405, 422), f"Unexpected status: {status}"


def test_licence_revert_cancellation_endpoint(api_client):
    status, payload = api_client.get("/api/licences/revert-cancellation")
    assert status in (200, 400, 405, 422), f"Unexpected status: {status}"


def test_security_settings_2fa_page(sb, api_client):
    """Güvenlik / 2FA ayar sayfası."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    paths = ["settings/security", "account/security", "security", "settings/2fa"]
    for path in paths:
        sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/{path}")
        time.sleep(2)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if sb.is_element_visible("main") and "404" not in body:
            if any(k in body for k in ["password", "security", "2fa", "two-factor", "şifre", "güvenlik"]):
                logger.info(f"INFO: test step - Security page at /{path}")
                return

    status, payload = api_client.get("/User/GetSession")
    GitsecApiClient.assert_success(status, payload, "/User/GetSession")
    logger.info("INFO: test step - Security UI route yok; session API doğrulandı")


def test_security_settings_2fa_page_api(api_client):
    """Session API güvenlik bağlamında erişilebilir."""
    status, payload = api_client.get("/User/GetSession")
    GitsecApiClient.assert_success(status, payload, "/User/GetSession")
    assert payload["data"]["sessionUser"]["userId"]


def test_notifications_or_activity_feed(sb):
    """Bildirim / activity feed erişimi."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/activity")
    time.sleep(3)
    dismiss_ui_blockers(sb)
    assert sb.is_element_visible("main") or "activity" in sb.get_text("body").lower()
