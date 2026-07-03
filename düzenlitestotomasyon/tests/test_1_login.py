import os
import sys
import time
import logging
import pytest

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from tests.helpers import perform_setup_and_login

logger = logging.getLogger("GitsecE2E")

def test_login_flow(sb):
    """
    1. LOGIN TEST
    - Navigates to the sign-in page.
    - Fills credentials from environment variables.
    - Handles manual Captcha solving if it appears.
    - Bypasses tour/onboarding guide using localStorage injection.
    - Closes optional KEP / overlay popups if they exist.
    - Asserts successful login.
    """
    logger.info("INFO: test step - Starting Login Test Flow")
    
    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://dev.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "754")
    
    assert email, "E2E_USER_EMAIL environment variable is not defined"
    assert password, "E2E_USER_PASSWORD environment variable is not defined"
    
    login_page = LoginPage(sb)
    loaded = login_page.load_session_cookies(base_url)
    
    if loaded:
        logger.info("INFO: test step - Reusing existing session cookies to bypass login")
        sb.open(f"{base_url}/{workspace_id}/dashboard")
        time.sleep(3)
        current_url = sb.get_current_url()
        is_404 = "404" in sb.get_text("body").lower() if sb.is_element_visible("body") else False
        if "sign-in" in current_url or is_404 or not sb.is_element_visible("main"):
            logger.info("INFO: test step - Session cookies expired. Attempting API login bypass...")
            loaded = login_page.api_login(base_url, email, password)
        else:
            login_page.bypass_onboarding()
            login_page.close_popups_if_any()
            
    if not loaded:
        logger.info("INFO: test step - No valid cookies found. Attempting API login bypass...")
        loaded = login_page.api_login(base_url, email, password)
        if not loaded:
            logger.info("INFO: test step - API login bypass failed. Falling back to fresh UI login...")
            login_page.navigate_to_login(base_url)
            login_page.login(email, password)
            login_page.bypass_onboarding()
            login_page.close_popups_if_any()
            login_page.save_session_cookies()
    
    logger.info("INFO: test step - Verifying URL contains workspace ID and dashboard path")
    expected_url_part = f"/{workspace_id}/"
    
    try:
        sb.wait_for_condition(lambda: expected_url_part in sb.get_current_url(), timeout=30)
    except Exception as e:
        logger.error(f"ERROR: URL did not update to expected path: {expected_url_part}. Current: {sb.get_current_url()}")
        raise e
        
    sb.assert_element("main", timeout=15)
    logger.info("INFO: test step - Login Test completed successfully!")
