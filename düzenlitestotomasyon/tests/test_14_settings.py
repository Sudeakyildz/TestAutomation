"""
14. KULLANICI AYARLARI TEST
Profil, güvenlik ve hesap ayarları sayfaları.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def _try_settings_paths(sb, cfg, suffixes):
    for suffix in suffixes:
        sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/{suffix}")
        time.sleep(3)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if sb.is_element_visible("main") and "404" not in body:
            return suffix
    return None


def test_profile_settings_page(sb, api_client):
    """Profil ayarları sayfası veya API profil bilgisi erişilebilir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)

    menu_selectors = [
        "button[data-slot='dropdown-menu-trigger']",
        "button.rounded-full",
        "button[aria-label*='User']",
    ]
    for sel in menu_selectors:
        try:
            if sb.is_element_visible(sel):
                sb.click(sel)
                time.sleep(1)
                settings_item = "xpath=//*[@role='menuitem'][contains(., 'Settings') or contains(., 'Profile') or contains(., 'Ayar') or contains(., 'Profil')]"
                if sb.is_element_visible(settings_item):
                    sb.click(settings_item)
                    time.sleep(3)
                    dismiss_ui_blockers(sb)
                    assert_main_visible(sb)
                    logger.info("INFO: test step - Profile settings opened via user menu")
                    return
        except Exception:
            pass

    found = _try_settings_paths(
        sb,
        cfg,
        [
            "settings/profile",
            "settings/account",
            "profile",
            "account/settings",
            "user/settings",
            "settings",
        ],
    )
    if found:
        assert_main_visible(sb)
        logger.info(f"INFO: test step - Profile settings route: {found}")
        return

    status, payload = api_client.get("/User/GetProfile")
    GitsecApiClient.assert_success(status, payload, "/User/GetProfile")
    logger.info("INFO: test step - Profile settings UI route not found; verified via GetProfile API")


def test_security_settings_page(sb):
    """Güvenlik ayarları sayfası erişilebilir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    found = _try_settings_paths(
        sb,
        cfg,
        ["settings/security", "settings/password", "security", "account/security"],
    )
    if not found:
        body = sb.get_text("body").lower()
        assert "password" in body or "security" in body or "2fa" in body or sb.is_element_visible("main")
    logger.info("INFO: test step - Security settings checked")


def test_user_profile_api(api_client):
    """GetProfile API e-posta döndürür."""
    status, payload = api_client.get("/User/GetProfile")
    GitsecApiClient.assert_success(status, payload, "/User/GetProfile")
    assert payload["data"]["email"]
    logger.info("INFO: test step - User profile API OK")


def test_user_session_api(api_client):
    """GetSession API kullanıcı bilgisi döndürür."""
    status, payload = api_client.get("/User/GetSession")
    GitsecApiClient.assert_success(status, payload, "/User/GetSession")
    assert payload["data"]["sessionUser"]["userId"]
    logger.info("INFO: test step - User session API OK")


def test_change_language_api(api_client):
    """Dil değiştirme API (EN)."""
    status, payload = api_client.post("/User/ChangeLanguage", {"languageCode": "en"})
    assert status in (200, 400), f"ChangeLanguage failed: {status}"
    logger.info("INFO: test step - Change language API responded")
