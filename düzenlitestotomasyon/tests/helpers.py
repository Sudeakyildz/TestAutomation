import os
import time
import logging
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

logger = logging.getLogger("GitsecE2E")

def perform_setup_and_login(sb):
    """Helper to perform dashboard login and return dashboard page object."""
    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://dev.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "754")
    
    login_page = LoginPage(sb)
    loaded = login_page.load_session_cookies(base_url)
    if loaded:
        logger.info("INFO: test step - Reusing existing session cookies to bypass login")
        sb.open(f"{base_url}/{workspace_id}/dashboard")
        time.sleep(3)
        current_url = sb.get_current_url()
        is_404 = "404" in sb.get_text("body").lower() if sb.is_element_visible("body") else False
        session_expired_modal = (
            sb.is_element_visible("div:contains('Session Expired')") or 
            sb.is_element_visible("button:contains('Sign In')") or
            sb.is_element_visible("h2:contains('Session Expired')") or
            "failed to load analytics" in sb.get_text("body").lower()
        )
        if "sign-in" in current_url or is_404 or not sb.is_element_visible("main") or session_expired_modal:
            logger.info("INFO: test step - Session expired or modal detected. Re-authenticating...")
            if sb.is_element_visible("button:contains('Sign In')"):
                try:
                    sb.click("button:contains('Sign In')")
                    time.sleep(2)
                except:
                    pass
            loaded = login_page.api_login(base_url, email, password)
            if loaded:
                sb.open(f"{base_url}/{workspace_id}/dashboard")
                login_page.save_session_cookies()
            
    if not loaded:
        logger.info("INFO: test step - No valid cookies found, doing full login / API bypass")
        loaded = login_page.api_login(base_url, email, password)
        if loaded:
            sb.open(f"{base_url}/{workspace_id}/dashboard")
            login_page.save_session_cookies()
        else:
            login_page.navigate_to_login(base_url)
            login_page.login(email, password)
            try:
                sb.wait_for_condition(lambda: f"/{workspace_id}/" in sb.get_current_url(), timeout=30)
            except Exception as e:
                logger.error(f"ERROR: Redirection to dashboard timed out: {str(e)}")
            
            login_page.bypass_onboarding()
            login_page.close_popups_if_any()
            login_page.save_session_cookies()
    
    try:
        sb.wait_for_condition(lambda: f"/{workspace_id}/" in sb.get_current_url(), timeout=15)
        sb.assert_element("main", timeout=15)
    except Exception as e:
        logger.error(f"ERROR: Dashboard loading check failed: {str(e)}")
        
    login_page.bypass_onboarding()
    login_page.close_popups_if_any()
    
    return DashboardPage(sb)

def scroll_table_right(sb):
    """Helper to scroll the repositories table container horizontally to make switches visible."""
    try:
        selectors = ["div.overflow-x-auto", "div.overflow-auto", ".overflow-x-scroll"]
        for sel in selectors:
            if sb.is_element_visible(sel):
                sb.execute_script(f"document.querySelector('{sel}').scrollLeft = 800")
                logger.info(f"INFO: test step - Scrolled table container right ({sel})")
                time.sleep(1)
                break
    except Exception as e:
        logger.warning(f"WARNING: Could not scroll table right: {str(e)}")

def check_license_limit_or_error(sb):
    """Checks if a license limit threshold or update error alert/toast is visible on the page."""
    try:
        body_text = sb.get_text("body").lower()
        error_keywords = [
            "licence limit within threshold",
            "failed to update repository status",
            "lisans limit",
            "threshold has been reached"
        ]
        for kw in error_keywords:
            if kw in body_text:
                logger.info(f"🚨 HATA/UYARI DETAYI: {kw.upper()} tespit edildi!")
                return True
    except:
        pass
    return False
