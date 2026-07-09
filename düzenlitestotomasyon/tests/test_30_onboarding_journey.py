"""
30. ONBOARDING JOURNEY
Ilk giris turu — bypass ve opsiyonel tour etkilesimi.
"""
import logging

import pytest

from pages.login_page import LoginPage
from tests.helpers import get_env_config, perform_setup_and_login, assert_main_visible, dismiss_ui_blockers
from utils.waits import wait_for_page_ready

logger = logging.getLogger("GitsecE2E")


def test_dashboard_loads_with_tour_bypass(sb):
    """Onboarding bypass sonrasi dashboard main icerigi yuklenir."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    assert cfg["workspace_id"] in sb.get_current_url()
    assert_main_visible(sb)
    logger.info("INFO: test step - Dashboard loaded with tour bypass")


def test_onboarding_tour_storage_injected(sb):
    """gs-tour localStorage onboarding bypass degeri enjekte edilir."""
    cfg = get_env_config()
    login_page = LoginPage(sb)
    sb.open(cfg["base_url"])
    login_page.bypass_onboarding()
    tour = sb.execute_script("return localStorage.getItem('gs-tour');")
    assert tour and "onboarding" in tour
    logger.info("INFO: test step - Onboarding tour bypass present in localStorage")


def test_help_tour_optional_interaction(sb):
    """Help/Tour butonu varsa acilir, yoksa test gecer."""
    from pages.dashboard_page import DashboardPage

    dashboard = perform_setup_and_login(sb)
    if dashboard.click_help():
        dismiss_ui_blockers(sb)
        assert_main_visible(sb)
        logger.info("INFO: test step - Help tour opened and dismissed")
    else:
        pytest.skip("Help/Tour button not available on this environment")


def test_signup_and_forgot_password_routes(sb):
    """Kayit ve sifremi unuttum sayfalari erisilebilir."""
    cfg = get_env_config()
    for path, keywords in (
        ("/sign-up", ("sign up", "register", "email", "kayit")),
        ("/forgot-password", ("password", "email", "sifre")),
    ):
        sb.open(f"{cfg['base_url']}{path}")
        wait_for_page_ready(sb)
        body = sb.get_text("body").lower()
        assert any(k in body for k in keywords), f"Expected content on {path}"
    logger.info("INFO: test step - Auth auxiliary routes OK")
