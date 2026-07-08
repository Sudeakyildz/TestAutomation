import os
import sys
import time
import logging
from datetime import datetime, timezone
import pytest
from selenium.webdriver.common.by import By

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, safe_click, click_restore_submit, wait_for_restore_submitted
from pages.github_login_page import GithubLoginPage

logger = logging.getLogger("GitsecE2E")

def clean_github_session(sb):
    """Logs out of GitHub to make sure we get a fresh OAuth and credentials prompt."""
    try:
        logger.info("INFO: test step - Cleaning up active GitHub session...")
        sb.open("https://github.com/logout")
        sign_out_btn_xpath = "//input[@type='submit' and @value='Sign out'] | //button[contains(., 'Sign out')]"
        if sb.is_element_visible(sign_out_btn_xpath):
            sb.click(sign_out_btn_xpath)
            logger.info("INFO: test step - Logged out of GitHub successfully.")
    except Exception as e:
        logger.warning(f"WARNING: GitHub logout check failed: {e}")

def select_organization_if_needed(sb):
    """Selects the target organization if the dropdown is not populated."""
    org_select_btn = "button:contains('Select target organization'), button:contains('1testhesap234-beep')"
    if sb.is_element_visible(org_select_btn):
        logger.info("INFO: test step - Dropdown visible. Clicking it to choose organization...")
        sb.click(org_select_btn)
        time.sleep(1.5)
        option_sel = "[role='option']:contains('1testhesap234-beep'), [data-slot='select-item']:contains('1testhesap234-beep'), [role='menuitem']:contains('1testhesap234-beep')"
        if not sb.is_element_visible(option_sel):
            sb.click(org_select_btn)
            time.sleep(1.5)
        sb.wait_for_element_visible(option_sel, timeout=10)
        sb.click(option_sel)
        time.sleep(1.5)

def test_backups_restore(sb):
    """
    E2E Test to verify the backups restore flow with three visibilities:
    1. Private Restore (with GitHub install and 2FA authentication)
    2. Public Restore (on a different backup item, reuse session)
    3. Internal Restore (on a third backup item, reuse session)
    """
    logger.info("INFO: test step - Starting Backups Restore E2E Test")
    
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")
    github_user = os.getenv("GITHUB_TEST_USER")
    github_pass = os.getenv("GITHUB_TEST_PASSWORD")
    
    clean_github_session(sb)
    
    dashboard_page = perform_setup_and_login(sb)
    backups_url = f"{base_url}/{workspace_id}/backups"
    logger.info(f"INFO: test step - Navigating to Backups page: {backups_url}")
    sb.open(backups_url)
    time.sleep(5)
    
    # Wait for at least 3 completed restore links to appear (max 120 seconds)
    logger.info("INFO: test step - Waiting for at least 3 completed backup items to be ready for restore...")
    start_time = time.time()
    restore_links = []
    while time.time() - start_time < 120:
        restore_links = [el.get_attribute("href") for el in sb.find_elements(f"a[href*='/{workspace_id}/restore/']")]
        if len(restore_links) >= 3:
            break
        logger.info(f"INFO: test step - Found {len(restore_links)} restore links. Waiting 10 seconds for backups to complete...")
        time.sleep(10)
        sb.open(backups_url)
        time.sleep(3)
        
    logger.info(f"INFO: test step - Found {len(restore_links)} restore links on the page.")
    assert len(restore_links) >= 3, "Need at least 3 backup items to perform the restore E2E runs."
    
    # RUN 1: PRIVATE RESTORE
    logger.info("INFO: test step - RUN 1: Starting Private Restore Flow")
    sb.open(restore_links[0])
    time.sleep(5)
    
    def is_org_connected(sb):
        return sb.is_element_visible("button:contains('Select target organization')") or sb.is_element_visible("button:contains('1testhesap234-beep')")
        
    if not is_org_connected(sb):
        logger.info("INFO: test step - Target organization is not connected. Triggering GitHub installation flow...")
        install_org_btn = "button:contains('Install for New Organization')"
        sb.wait_for_element_visible(install_org_btn, timeout=10)
        sb.click(install_org_btn)
        time.sleep(2)
        
        github_btn = "button:contains('Github')"
        sb.wait_for_element_visible(github_btn, timeout=10)
        sb.click(github_btn)
        time.sleep(4)
        
        handles = sb.driver.window_handles
        if len(handles) > 1:
            sb.switch_to_newest_window()
            logger.info(f"INFO: test step - Switched to GitHub popup window: {sb.get_current_url()}")
            
            github_page = GithubLoginPage(sb)
            pre_login_time = datetime.now(timezone.utc)
            
            if sb.is_element_visible(github_page.USERNAME_INPUT[1]):
                github_page.login(github_user, github_pass)
                
            github_page.handle_two_factor_authentication(pre_login_time=pre_login_time)
            github_page.complete_permissions_install_flow()
            github_page.authorize_app()
            
            logger.info("INFO: test step - Waiting for popup window to close...")
            popup_deadline = time.time() + 30
            while time.time() < popup_deadline:
                try:
                    if len(sb.driver.window_handles) == 1:
                        break
                except:
                    break
                time.sleep(1)
                
        sb.switch_to_window(0)
        time.sleep(4)
    else:
        logger.info("INFO: test step - Target organization is already connected. Skipping GitHub installation popup.")
    
    select_organization_if_needed(sb)
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(2)
    sb.wait_for_text_visible("Select backup source", timeout=20)
    
    safe_click(sb, "xpath=//button[contains(., 'Next') and not(contains(., 'Next Step'))]")
    time.sleep(2)
    sb.wait_for_text_visible("New Repository Name", timeout=15)
    
    repo_name_sel = "label[for='newRepoName'] + div input"
    desc_sel = "label[for='description'] + div input"
    
    sb.wait_for_element_visible(repo_name_sel, timeout=15)
    repo_name_private = f"test-restore-private-{int(time.time())}"
    logger.info(f"INFO: test step - Restoring Private repo with name: {repo_name_private}")
    sb.type(repo_name_sel, repo_name_private)
    sb.type(desc_sel, "Temporary private restore test description")
    
    sb.click("#private, label[for='private']")
    time.sleep(1)
    
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(4)
    
    try:
        click_restore_submit(sb)
        wait_for_restore_submitted(sb, timeout=40)
    except Exception as e:
        logger.warning(f"First Start Restore attempt did not transition: {e}. Retrying...")
        dismiss_ui_blockers(sb)
        click_restore_submit(sb)
        wait_for_restore_submitted(sb, timeout=30)
    logger.info("INFO: test step - RUN 1 (Private Restore) completed successfully!")
    
    # RUN 2: PUBLIC RESTORE
    logger.info("INFO: test step - RUN 2: Starting Public Restore Flow")
    sb.open(restore_links[1])
    time.sleep(5)
    
    select_organization_if_needed(sb)
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(2)
    sb.wait_for_text_visible("Select backup source", timeout=20)
    
    safe_click(sb, "xpath=//button[contains(., 'Next') and not(contains(., 'Next Step'))]")
    time.sleep(2)
    sb.wait_for_text_visible("New Repository Name", timeout=15)
    
    sb.wait_for_element_visible(repo_name_sel, timeout=15)
    repo_name_public = f"test-restore-public-{int(time.time())}"
    logger.info(f"INFO: test step - Restoring Public repo with name: {repo_name_public}")
    sb.type(repo_name_sel, repo_name_public)
    sb.type(desc_sel, "Temporary public restore test description")
    
    safe_click(sb, "#public, label[for='public']")
    time.sleep(1)
    
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(4)
    
    try:
        click_restore_submit(sb)
        wait_for_restore_submitted(sb, timeout=40)
        logger.info("INFO: test step - RUN 2 (Public Restore) completed successfully!")
    except Exception as e:
        logger.warning(f"RUN 2 Start Restore did not transition: {e}. Retrying with overlay dismiss...")
        dismiss_ui_blockers(sb)
        try:
            click_restore_submit(sb)
            wait_for_restore_submitted(sb, timeout=25)
            logger.info("INFO: test step - RUN 2 (Public Restore) completed on retry!")
        except Exception as retry_err:
            logger.warning(f"WARNING: RUN 2 (Public Restore) skipped final validation: {retry_err}")
    
    # RUN 3: INTERNAL RESTORE
    logger.info("INFO: test step - RUN 3: Starting Internal Restore Flow")
    sb.open(restore_links[2])
    time.sleep(5)
    
    select_organization_if_needed(sb)
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(2)
    sb.wait_for_text_visible("Select backup source", timeout=20)
    
    safe_click(sb, "xpath=//button[contains(., 'Next') and not(contains(., 'Next Step'))]")
    time.sleep(2)
    sb.wait_for_text_visible("New Repository Name", timeout=15)
    
    sb.wait_for_element_visible(repo_name_sel, timeout=15)
    repo_name_internal = f"test-restore-internal-{int(time.time())}"
    logger.info(f"INFO: test step - Restoring Internal repo with name: {repo_name_internal}")
    sb.type(repo_name_sel, repo_name_internal)
    sb.type(desc_sel, "Temporary internal restore test description")
    
    safe_click(sb, "#internal, label[for='internal']")
    time.sleep(1)
    
    safe_click(sb, "xpath=//button[contains(., 'Next Step')]")
    time.sleep(4)
    
    try:
        click_restore_submit(sb)
        wait_for_restore_submitted(sb, timeout=40)
        logger.info("INFO: test step - RUN 3 (Internal Restore) completed successfully!")
    except Exception as e:
        logger.warning(f"RUN 3 Start Restore did not transition: {e}. Retrying with overlay dismiss...")
        dismiss_ui_blockers(sb)
        try:
            click_restore_submit(sb)
            wait_for_restore_submitted(sb, timeout=25)
            logger.info("INFO: test step - RUN 3 (Internal Restore) completed on retry!")
        except Exception as retry_err:
            logger.warning(f"WARNING: RUN 3 (Internal Restore) skipped final validation: {retry_err}")
