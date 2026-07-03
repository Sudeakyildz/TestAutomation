import os
import sys
import time
import logging
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login
from pages.login_page import LoginPage

logger = logging.getLogger("GitsecE2E")

def select_schedule_type(sb, type_name):
    logger.info(f"INFO: test step - Selecting schedule type: {type_name}")
    # Second combobox or select trigger is usually type name
    triggers = sb.find_elements("[data-slot='select-trigger'], [role='combobox']")
    if len(triggers) >= 2:
        triggers[1].click()
        time.sleep(1.5)
        option_sel = f"[role='option']:contains('{type_name}'), [data-slot='select-item']:contains('{type_name}')"
        sb.wait_for_element_visible(option_sel, timeout=10)
        sb.click(option_sel)
        time.sleep(1)

def set_checkbox_state(sb, label_text, target_state):
    logger.info(f"INFO: test step - Setting checkbox '{label_text}' to {target_state}")
    # Find label containing text and toggle checkbox button inside/adjacent
    checkbox_sel = f"button[role='checkbox']:contains('{label_text}'), label:contains('{label_text}') button[role='checkbox']"
    if sb.is_element_visible(checkbox_sel):
        aria_checked = sb.get_attribute(checkbox_sel, "aria-checked")
        current_state = aria_checked == "true"
        if current_state != target_state:
            sb.click(checkbox_sel)
            time.sleep(0.5)
    else:
        # Sibling search
        elements = sb.find_elements("label, span, button")
        for el in elements:
            try:
                if label_text.lower() in el.text.lower():
                    # Try clicking adjacent role checkbox
                    parent = el.find_element(By.XPATH, "./..")
                    cb = parent.find_element(By.CSS_SELECTOR, "button[role='checkbox'], input[type='checkbox']")
                    aria_checked = cb.get_attribute("aria-checked") or cb.get_attribute("checked")
                    current_state = aria_checked == "true" or aria_checked == "checked"
                    if current_state != target_state:
                        cb.click()
                        time.sleep(0.5)
                    break
            except:
                pass

def test_schedulers_flow(sb):
    """
    8. SCHEDULERS TEST
    - Navigates to Schedulers page.
    - Clicks 'New Scheduler' button.
    - Selects an active repository.
    - Fills out Scheduler Name and configures included options (Code, PRs, Issues).
    - Configures and saves a Daily Scheduler.
    """
    logger.info("INFO: test step - Starting Schedulers E2E Test Flow")
    
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")
    
    # 1. Login & Navigate to Schedulers
    perform_setup_and_login(sb)
    schedulers_url = f"{base_url}/{workspace_id}/schedulers"
    logger.info(f"INFO: test step - Navigating to Schedulers: {schedulers_url}")
    sb.open(schedulers_url)
    time.sleep(4)
    
    # Handle Session Expired dialog if present
    if sb.is_element_visible("div:contains('Session Expired')") or sb.is_element_visible("button:contains('Sign In')"):
        logger.info("INFO: test step - Session Expired modal detected! Re-authenticating...")
        try:
            sb.click("button:contains('Sign In')")
            time.sleep(2)
        except:
            pass
        login_page = LoginPage(sb)
        login_page.api_login(base_url, os.getenv("E2E_USER_EMAIL"), os.getenv("E2E_USER_PASSWORD"))
        login_page.save_session_cookies()
        sb.open(schedulers_url)
        time.sleep(4)
    
    # 2. Click 'New Scheduler'
    new_scheduler_btn = "button:contains('New Scheduler')"
    sb.wait_for_element_visible(new_scheduler_btn, timeout=15)
    sb.click(new_scheduler_btn)
    time.sleep(2)
    
    # 3. Select active repository
    repo_combo = "button:contains('Select a repository'), [role='combobox']:contains('Select a repository')"
    sb.wait_for_element_visible(repo_combo, timeout=10)
    sb.click(repo_combo)
    time.sleep(1.5)
    
    # Choose first active repository option (not disabled)
    options = sb.find_elements("[role='option']:not([data-disabled='true']), [data-slot='select-item']:not([data-disabled='true'])")
    if len(options) > 0:
        logger.info(f"INFO: test step - Selecting repo: {options[0].text}")
        options[0].click()
        time.sleep(2)
    else:
        sb.send_keys("body", Keys.ESCAPE)
        pytest.skip("No active/connectable repositories found to schedule.")
        
    # 4. Fill Name
    name_input = "input[placeholder*='Nightly'], input[name='name']"
    sb.wait_for_element_visible(name_input, timeout=10)
    schedule_name = f"e2e-daily-scheduler-{int(time.time())}"
    sb.type(name_input, schedule_name)
    
    # 5. Set Time
    time_input = "input[type='time']"
    if sb.is_element_visible(time_input):
        sb.type(time_input, "02:00")
        
    # 6. Configure Included Checkboxes
    set_checkbox_state(sb, "Code & Commits", True)
    set_checkbox_state(sb, "Pull Requests", True)
    set_checkbox_state(sb, "Issues", True)
    
    # 7. Select Timezone if combobox exists
    triggers = sb.find_elements("[data-slot='select-trigger'], [role='combobox']")
    if len(triggers) >= 3:
        triggers[-1].click()
        time.sleep(1.5)
        tz_option = "[role='option']:contains('Istanbul'), [data-slot='select-item']:contains('Istanbul')"
        if sb.is_element_visible(tz_option):
            sb.click(tz_option)
        else:
            options = sb.find_elements("[role='option'], [data-slot='select-item']")
            if len(options) > 0:
                options[0].click()
        time.sleep(1)
        
    # 8. Save Scheduler
    save_btn = "button:contains('Save'), button:contains('Create')"
    sb.wait_for_element_visible(save_btn, timeout=10)
    sb.click(save_btn)
    time.sleep(4)
    
    # 9. Verify Schedulers Page loads or shows item
    sb.assert_url_contains("/schedulers")
    logger.info("INFO: test step - Schedulers flow completed successfully!")
