import os
import sys
import time
import logging
import pytest

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from tests.helpers import perform_setup_and_login, scroll_table_right

logger = logging.getLogger("GitsecE2E")

def set_checkbox_states(sb, code_commits, pull_requests, issues):
    """Sets the checkboxes in the backup modal to the desired state."""
    selectors = [
        ("div[role='dialog'] div.grid-cols-1 label:nth-child(1) button[role='checkbox']", code_commits, "Code & Commits"),
        ("div[role='dialog'] div.grid-cols-1 label:nth-child(2) button[role='checkbox']", pull_requests, "Pull Requests"),
        ("div[role='dialog'] div.grid-cols-1 label:nth-child(3) button[role='checkbox']", issues, "Issues")
    ]
    for sel, target_state, label in selectors:
        sb.wait_for_element_visible(sel, timeout=5)
        aria_checked = sb.get_attribute(sel, "aria-checked")
        current_state = aria_checked == "true"
        if current_state != target_state:
            logger.info(f"INFO: test step - Toggling '{label}' from {current_state} to {target_state}")
            sb.click(sel)
            time.sleep(0.5)

def test_github_backup_combinations(sb):
    """
    E2E Test to verify backup configurations with all 7 requested item combinations.
    """
    logger.info("INFO: test step - Starting GitHub Repository Backup Combinations Test")
    
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")
    
    dashboard_page = perform_setup_and_login(sb)
    github_repos_url = f"{base_url}/{workspace_id}/repositories/github"
    
    scenarios = [
        (11, True, False, False),   # Only Code & Commits
        (10, False, True, False),   # Only Pull Requests
        (9,  False, False, True),   # Only Issues
        (8,  True,  True,  False),  # Code & Commits + Pull Requests
        (7,  True,  False, True),   # Code & Commits + Issues
        (6,  False, True,  True),   # Pull Requests + Issues
        (5,  True,  True,  True)    # All items
    ]
    
    for sc_num, code_commits, pull_requests, issues in scenarios:
        logger.info(f"\n==================================================")
        logger.info(f"RUNNING SCENARIO {sc_num}: Code&Commits={code_commits}, PullRequests={pull_requests}, Issues={issues}")
        logger.info(f"==================================================")
        
        sb.open(github_repos_url)
        time.sleep(4)
        
        sb.assert_element("table", timeout=30)
        scroll_table_right(sb)
        
        first_row_switch = "table tbody tr:nth-child(1) button[role='switch']"
        sb.wait_for_element_visible(first_row_switch, timeout=15)
        
        aria_checked = sb.get_attribute(first_row_switch, "aria-checked")
        if aria_checked != "true":
            logger.info("INFO: test step - First repository is not included. Toggling to active...")
            sb.scroll_to(first_row_switch)
            time.sleep(0.5)
            sb.click(first_row_switch)
            time.sleep(2)
            
            body_text = sb.get_text("body").lower()
            if "licence limit" in body_text or "failed to update" in body_text:
                logger.warning("WARNING: License limit threshold reached; cannot include first repository.")
                pytest.skip("Skipping scenario: License limit threshold reached.")
                
            sb.wait_for_condition(lambda: sb.get_attribute(first_row_switch, "aria-checked") == "true", timeout=15)
            logger.info("INFO: test step - First repository included successfully.")
            scroll_table_right(sb)
            
        backup_now_btn = "table tbody tr:nth-child(1) button[data-slot='dialog-trigger']"
        sb.wait_for_element_visible(backup_now_btn, timeout=15)
        logger.info("INFO: test step - Clicking 'Backup now' button...")
        sb.scroll_to(backup_now_btn)
        time.sleep(0.5)
        sb.click(backup_now_btn)
        time.sleep(2)
        
        sb.wait_for_element_visible("div[role='dialog']", timeout=10)
        logger.info("INFO: test step - Backup modal dialog opened.")
        
        set_checkbox_states(sb, code_commits, pull_requests, issues)
        time.sleep(1)
        
        submit_btn = "div[role='dialog'] button[type='submit']"
        sb.wait_for_element_visible(submit_btn, timeout=5)
        logger.info("INFO: test step - Clicking 'Start Backup' button...")
        sb.click(submit_btn)
        
        sb.wait_for_text_visible("Backup started successfully!", timeout=15)
        logger.info(f"SUCCESS: Scenario {sc_num} completed successfully! Toast verified.")
        time.sleep(2)
        
    logger.info("\n==================================================")
    logger.info("ALL 7 BACKUP COMBINATIONS PASSED SUCCESSFULLY!")
    logger.info("==================================================")
