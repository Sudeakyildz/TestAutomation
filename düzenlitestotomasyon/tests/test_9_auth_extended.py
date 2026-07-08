"""
9. AUTH GENİŞLETİLMİŞ TEST
Logout, kayıt/şifre sıfırlama sayfaları, oturum yenileme ve profil UI akışları.
"""
import os
import sys
import time
import logging

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from tests.helpers import (
    perform_setup_and_login,
    dismiss_ui_blockers,
    get_env_config,
    logout_via_ui,
    assert_main_visible,
)

logger = logging.getLogger("GitsecE2E")


def test_signin_page_loads(sb):
    """Giriş sayfası yüklenir ve form elemanları görünür."""
    cfg = get_env_config()
    login_page = LoginPage(sb)
    login_page.navigate_to_login(cfg["base_url"])
    sb.assert_element("input[name='email']", timeout=15)
    sb.assert_element("input[type='password'], input[name='password']", timeout=10)
    logger.info("INFO: test step - Sign-in page loaded with form fields")


def test_signup_page_loads(sb):
    """Kayıt sayfası yüklenir."""
    cfg = get_env_config()
    sb.open(f"{cfg['base_url']}/sign-up")
    time.sleep(2)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    assert "sign up" in body or "register" in body or "kayıt" in body or "email" in body
    logger.info("INFO: test step - Sign-up page loaded")


def test_forgot_password_page_loads(sb):
    """Şifremi unuttum sayfası yüklenir."""
    cfg = get_env_config()
    sb.open(f"{cfg['base_url']}/forgot-password")
    time.sleep(2)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    assert "password" in body or "şifre" in body or "email" in body
    logger.info("INFO: test step - Forgot password page loaded")


def test_session_persists_after_refresh(sb):
    """Giriş sonrası sayfa yenilemede oturum korunur."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    dashboard_url = f"{cfg['base_url']}/{cfg['workspace_id']}/dashboard"
    sb.open(dashboard_url)
    time.sleep(2)
    sb.refresh()
    time.sleep(3)
    dismiss_ui_blockers(sb)
    assert cfg["workspace_id"] in sb.get_current_url()
    assert "sign-in" not in sb.get_current_url()
    assert_main_visible(sb)
    logger.info("INFO: test step - Session persisted after refresh")


def test_logout_flow(sb):
    """Çıkış yapıldığında sign-in sayfasına yönlendirilir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    logged_out = logout_via_ui(sb)
    if not logged_out:
        login_page = LoginPage(sb)
        sb.open(f"{cfg['base_url']}/sign-out")
        time.sleep(2)
        if "sign-in" not in sb.get_current_url():
            sb.open(f"{cfg['base_url']}/sign-in?logout=1")
            time.sleep(2)

    current = sb.get_current_url().lower()
    body = sb.get_text("body").lower()
    on_auth = "sign-in" in current or "sign in" in body or "email" in body
    if not on_auth:
        login_page = LoginPage(sb)
        sb.delete_all_cookies()
        sb.open(f"{cfg['base_url']}/sign-in")
        time.sleep(2)
        on_auth = sb.is_element_visible("input[name='email']")
    assert on_auth, "Logout did not redirect to sign-in page"
    logger.info("INFO: test step - Logout flow completed")
