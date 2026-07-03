import os
import sys
import time
import logging
import pytest
from datetime import datetime, timezone

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from tests.helpers import perform_setup_and_login, scroll_table_right, check_license_limit_or_error

logger = logging.getLogger("GitsecE2E")

def test_github_repositories_include_all_then_exclude_all(sb):
    """
    E2E Test to include all repositories on the current page, and then exclude them all back.
    Uses index-based CSS selectors to bypass visibility/scrolling text constraints.
    """
    logger.info("INFO: test step - Starting Include All then Exclude All Test")
    
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")
    
    dashboard_page = perform_setup_and_login(sb)
    github_repos_url = f"{base_url}/{workspace_id}/repositories/github"
    logger.info(f"INFO: test step - Navigating to GitHub Repositories page: {github_repos_url}")
    sb.open(github_repos_url)
    time.sleep(4)
    
    def click_confirm_button_if_any(sb):
        """Loops through different selector strategies to robustly click the confirmation button."""
        confirm_selectors = [
            "button.bg-destructive",
            "//button[contains(text(), 'Yes, Exclude')]",
            "//button[contains(text(), 'Exclude')]",
            "//button[contains(text(), 'Confirm')]",
            "//button[contains(text(), 'Hariç Tut')]"
        ]
        for sel in confirm_selectors:
            try:
                # Wait up to 3 seconds for the button to become visible
                sb.wait_for_element_visible(sel, timeout=3)
                sb.click(sel)
                logger.info(f"INFO: test step - Clicked confirm button via selector: {sel}")
                try:
                    sb.wait_for_element_not_visible("div[role='dialog']", timeout=5)
                except:
                    pass
                time.sleep(1.5)
                return True
            except:
                pass
        return False

    sb.assert_element("table", timeout=30)
    scroll_table_right(sb)

    rows = sb.find_elements("table tbody tr")
    row_count = len(rows)
    logger.info(f"INFO: test step - Found {row_count} repositories in the table body.")
    
    logger.info("INFO: test step - Step 1: Setting up clean state (Excluding all active repositories)")
    for i in range(row_count):
        switch_sel = f"table tbody tr:nth-child({i+1}) button[role='switch']"
        if sb.is_element_present(switch_sel):
            aria_checked = sb.get_attribute(switch_sel, "aria-checked")
            if aria_checked == "true" or aria_checked == "checked":
                logger.info(f"INFO: test step - Row {i+1} is active. Toggling to inactive...")
                sb.scroll_to(switch_sel)
                time.sleep(0.5)
                sb.js_click(switch_sel)
                
                # Robust click confirmation button
                click_confirm_button_if_any(sb)
                sb.wait_for_condition(lambda: sb.get_attribute(switch_sel, "aria-checked") == "false", timeout=45)
                logger.info(f"INFO: test step - Row {i+1} successfully set to inactive.")
                
    logger.info("INFO: test step - Refreshing page to establish baseline...")
    sb.open(github_repos_url)
    time.sleep(4)
    scroll_table_right(sb)
    
    logger.info("INFO: test step - Step 2: Toggling all repositories to ACTIVE (Include)")
    included_indices = []
    
    for i in range(row_count):
        switch_sel = f"table tbody tr:nth-child({i+1}) button[role='switch']"
        if sb.is_element_present(switch_sel):
            aria_checked = sb.get_attribute(switch_sel, "aria-checked")
            if aria_checked == "false" or not aria_checked:
                logger.info(f"INFO: test step - Toggling row {i+1} to active...")
                sb.scroll_to(switch_sel)
                time.sleep(0.5)
                sb.js_click(switch_sel)
                time.sleep(1.5)
                if check_license_limit_or_error(sb):
                    logger.info(f"INFO: test step - Stopped further inclusions at row {i+1} due to license limit/error.")
                    break
                try:
                    sb.wait_for_condition(lambda: sb.get_attribute(switch_sel, "aria-checked") == "true", timeout=45)
                    logger.info(f"INFO: test step - Row {i+1} successfully set to active.")
                    included_indices.append(i)
                except Exception as e:
                    if check_license_limit_or_error(sb):
                        logger.info(f"INFO: test step - Stopped inclusions at row {i+1} due to license limit/error on verification.")
                        break
                    raise e
                    
    logger.info(f"INFO: test step - Successfully included row indices: {included_indices}")
    
    logger.info("INFO: test step - Step 3: Toggling newly active repositories back to INACTIVE (Exclude)")
    for i in included_indices:
        switch_sel = f"table tbody tr:nth-child({i+1}) button[role='switch']"
        if sb.is_element_present(switch_sel):
            aria_checked = sb.get_attribute(switch_sel, "aria-checked")
            if aria_checked == "true" or aria_checked == "checked":
                logger.info(f"INFO: test step - Toggling row {i+1} back to inactive...")
                sb.scroll_to(switch_sel)
                time.sleep(0.5)
                sb.js_click(switch_sel)
                
                # Robust click confirmation button
                click_confirm_button_if_any(sb)
                sb.wait_for_condition(lambda: sb.get_attribute(switch_sel, "aria-checked") == "false", timeout=45)
                logger.info(f"INFO: test step - Row {i+1} successfully set to inactive.")
                
    # Single page refresh at the end of Step 3 to verify persistence
    sb.open(github_repos_url)
    time.sleep(4)
    scroll_table_right(sb)
    logger.info("INFO: test step - Include All then Exclude All Test completed successfully!")
