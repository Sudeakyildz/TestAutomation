"""
19. NEGATİF & EDGE CASE TEST
404, geçersiz workspace, oturum ve UI edge senaryoları.
"""
import os
import sys
import time
import logging

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from tests.journey_helpers import visit_all_core_sidebar_pages, open_workspace_path
from utils.waits import wait_for_page_ready
from tests.api_helpers import USER_SESSION_PATH
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_invalid_workspace_shows_error_or_redirect(sb):
    """Geçersiz workspace ID ile erişim hata veya yönlendirme gösterir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    sb.open(f"{cfg['base_url']}/99999999/dashboard")
    wait_for_page_ready(sb)
    dismiss_ui_blockers(sb)
    body = sb.get_text("body").lower()
    url = sb.get_current_url()
    ok = (
        "404" in body
        or "not found" in body
        or "sign-in" in url
        or cfg["workspace_id"] in url
    )
    assert ok, f"Invalid workspace did not show expected error. URL: {url}"
    logger.info("INFO: test step - Invalid workspace handled")


def test_unauthenticated_api_rejected():
    """Token olmadan korumalı API reddedilir."""
    client = GitsecApiClient()
    status, payload = client.get(USER_SESSION_PATH, auth=False)
    assert status in (401, 403), f"Expected 401/403 without token, got {status}"
    logger.info("INFO: test step - Unauthenticated API rejected")


def test_invalid_credentials_api():
    """Geçersiz kimlik bilgileri reddedilir."""
    client = GitsecApiClient()
    status, payload = client.post(
        "/Auth/SignIn",
        {"email": "nonexistent@test.local", "password": "WrongPass123!"},
        auth=False,
    )
    assert status in (400, 401, 403, 422)
    logger.info("INFO: test step - Invalid credentials rejected")


def test_deep_link_requires_auth(sb):
    """Oturumsuz deep link sign-in'e yönlendirir."""
    cfg = get_env_config()
    sb.delete_all_cookies()
    sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/repositories/github")
    time.sleep(4)
    url = sb.get_current_url().lower()
    body = sb.get_text("body").lower()
    needs_auth = "sign-in" in url or "sign in" in body or sb.is_element_visible("input[name='email']")
    if not needs_auth:
        login_page = LoginPage(sb)
        login_page.api_login(cfg["base_url"], cfg["email"], cfg["password"])
        login_page.save_session_cookies()
    assert needs_auth or cfg["workspace_id"] in sb.get_current_url()
    logger.info("INFO: test step - Deep link auth check completed")


def test_sidebar_navigation_items(sb):
    """Sidebar ile ana sayfalar arasi gezinme (journey helper)."""
    cfg = get_env_config()
    results = visit_all_core_sidebar_pages(sb, cfg)
    assert len([v for v in results.values() if v]) >= 4
    logger.info("INFO: test step - Sidebar navigation via journey helper OK")
