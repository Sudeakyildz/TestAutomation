import os
import time
import logging
from datetime import datetime, timezone
import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.github_login_page import GithubLoginPage
from tests.helpers import perform_setup_and_login

logger = logging.getLogger("GitsecE2E")

def test_github_repositories_connection(sb):
    """
    E2E Test to connect/reconnect GitHub provider and access repositories page.
    """
    logger.info("INFO: test step - Starting GitHub Repositories Connection Test")
    
    github_user = os.getenv("GITHUB_TEST_USER")
    github_pass = os.getenv("GITHUB_TEST_PASSWORD")
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://dev.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "754")
    
    if not github_user or not github_pass:
        pytest.skip("GITHUB_TEST_USER or GITHUB_TEST_PASSWORD is not set in .env. Skipping test.")
        
    try:
        logger.info("INFO: test step - Navigating to GitHub to clear active session...")
        sb.open("https://github.com/logout")
        sign_out_btn_xpath = "//input[@type='submit' and @value='Sign out'] | //button[contains(., 'Sign out')]"
        if sb.is_element_visible(sign_out_btn_xpath):
            sb.click(sign_out_btn_xpath)
            logger.info("INFO: test step - Logged out of GitHub successfully.")
    except Exception as e:
        logger.warning(f"WARNING: GitHub logout check failed: {str(e)}")
        
    dashboard_page = perform_setup_and_login(sb)
    add_provider_url = f"{base_url}/{workspace_id}/repositories/add"
    logger.info(f"INFO: test step - Navigating to Add Provider page: {add_provider_url}")
    sb.open(add_provider_url)
    
    is_connected = False
    try:
        rows = sb.find_elements("tr")
        for r in rows:
            if "github" in r.text.lower():
                is_connected = "active" in r.text.lower()
                logger.info(f"INFO: test step - GitHub connection state: {'Active' if is_connected else 'Inactive'}")
                break
    except Exception as e:
        logger.info(f"INFO: test step - GitHub integration row search failed: {e}")
        
    if is_connected:
        logger.info("INFO: test step - GitHub already connected. Attempting to disconnect for clean run...")
        try:
            for opt in ["Disconnect", "Remove", "Configure"]:
                sel = f"button:contains('{opt}')"
                if sb.is_element_present(sel):
                    sb.click(sel)
                    break
            time.sleep(2)
            for opt in ["Confirm", "Disconnect", "Yes"]:
                sel_confirm = f"button:contains('{opt}')"
                if sb.is_element_present(sel_confirm):
                    sb.click(sel_confirm)
                    break
            time.sleep(4)
            logger.info("INFO: test step - Disconnected active GitHub provider successfully.")
        except Exception as e:
            logger.warning(f"WARNING: Disconnecting active provider failed: {str(e)}")
            
    sb.open(add_provider_url)
    logger.info("INFO: test step - Finding GitHub connection button...")
    connect_btn_css = "button[class*='group/btn']"
    
    sb.wait_for_element_visible(connect_btn_css, timeout=15)
    sb.scroll_to(connect_btn_css)
    time.sleep(0.5)
    
    logger.info("INFO: test step - Clicking GitHub connect button...")
    try:
        sb.click(connect_btn_css)
    except Exception as e:
        logger.warning(f"WARNING: Standard click failed: {str(e)}")
        
    time.sleep(4)
    
    try:
        handles = sb.driver.window_handles
        logger.info(f"INFO: test step - Window handles: {handles}")
        if len(handles) == 1:
            logger.warning("WARNING: Standard click did not open a new window. Trying JS click...")
            sb.js_click(connect_btn_css)
            time.sleep(4)
            handles = sb.driver.window_handles
            logger.info(f"INFO: test step - Window handles after JS click: {handles}")
    except Exception as e:
        logger.warning(f"WARNING: Could not check/process window handles: {str(e)}")
        
    try:
        sb.switch_to_newest_window()
        logger.info(f"INFO: test step - Switched to newest window. URL: {sb.get_current_url()}")
    except Exception as e:
        logger.error(f"ERROR: Failed to switch to window: {str(e)}")
        
    try:
        sb.wait_for_condition(lambda: "github.com" in sb.get_current_url(), timeout=15)
        logger.info("INFO: test step - Successfully loaded github.com in popup window")
    except Exception as e:
        logger.error(f"ERROR: Wait for github.com timed out. Current URL: {sb.get_current_url()}")
        raise e
    
    github_page = GithubLoginPage(sb)
    pre_login_time = datetime.now(timezone.utc)
    
    try:
        if sb.is_element_visible(github_page.USERNAME_INPUT[1]):
            github_page.login(github_user, github_pass)
            
        github_page.handle_two_factor_authentication(pre_login_time=pre_login_time)
        github_page.complete_permissions_install_flow()
        github_page.authorize_app()
        
        logger.info("INFO: test step - Waiting for OAuth flow to complete and popup window to close...")
        popup_deadline = time.time() + 30
        while time.time() < popup_deadline:
            try:
                if len(sb.driver.window_handles) == 1:
                    break
                if "gitsec.io" in sb.get_current_url():
                    logger.info("INFO: test step - Redirect to gitsec.io detected. Flow complete.")
                    break
            except:
                break
            time.sleep(1)
    finally:
        try:
            sb.switch_to_window(0)
        except Exception as se:
            logger.warning(f"WARNING: Switch back to original window failed: {str(se)}")
        time.sleep(3)
        
    logger.info("INFO: test step - Verifying GitHub is successfully connected in Dashboard...")
    sb.open(add_provider_url)
    
    try:
        def check_active_status():
            rows = sb.find_elements("tr")
            for r in rows:
                if "github" in r.text.lower() and "active" in r.text.lower():
                    return True
            return False
            
        sb.wait_for_condition(check_active_status, timeout=15)
        logger.info("INFO: test step - GitHub provider connection verified successfully!")
    except Exception as e:
        logger.error(f"ERROR: Failed to verify GitHub active status: {str(e)}")
        raise e
        
    logger.info("INFO: test step - GitHub Repositories Connection Test completed successfully!")
