import os
import sys
import time
import logging
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, safe_click
from pages.login_page import LoginPage

logger = logging.getLogger("GitsecE2E")


def find_button_by_text(sb, *texts, root=None):
    scope = root if root is not None else sb.driver
    buttons = scope.find_elements(By.CSS_SELECTOR, "button") if hasattr(scope, "find_elements") else sb.find_elements("button")
    for btn in buttons:
        try:
            label = (btn.text or "").strip().lower()
            if any(t.lower() in label for t in texts):
                return btn
        except Exception:
            pass
    return None


def open_new_scheduler_modal(sb):
    dismiss_ui_blockers(sb)
    btn = find_button_by_text(sb, "New Scheduler", "Create Scheduler")
    if btn is None:
        btn = sb.find_element("xpath=//button[contains(., 'New Scheduler') or contains(., 'Create Scheduler')]")
    sb.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    time.sleep(0.5)
    try:
        btn.click()
    except Exception:
        sb.execute_script("arguments[0].click();", btn)
    time.sleep(2)
    sb.wait_for_element_visible("[data-slot='dialog-content']", timeout=10)


def select_repository_from_modal(sb):
    repo_trigger = "[data-slot='dialog-content'] button[data-slot='popover-trigger']"
    sb.wait_for_element_visible(repo_trigger, timeout=10)
    safe_click(sb, repo_trigger, timeout=10, dismiss=False)
    time.sleep(1.5)

    search_selectors = [
        "[cmdk-input]",
        "input[placeholder*='Search']",
        "input[placeholder*='repository']",
    ]
    for sel in search_selectors:
        if sb.is_element_visible(sel):
            sb.type(sel, "test")
            time.sleep(1.5)
            break

    option_selectors = [
        "[cmdk-item]",
        "[role='dialog'] [role='option']",
        "[role='dialog'] [data-slot='command-item']",
    ]
    option = None
    for sel in option_selectors:
        items = sb.find_elements(sel)
        visible = [el for el in items if el.is_displayed() and "/" in (el.text or "")]
        if visible:
            option = visible[0]
            break

    if option is None:
        dialogs = sb.find_elements("[role='dialog']")
        for dialog in reversed(dialogs):
            try:
                candidates = dialog.find_elements(By.CSS_SELECTOR, "button, [role='option'], li")
                for cand in candidates:
                    txt = (cand.text or "").strip()
                    if "/" in txt and len(txt) > 3 and cand.is_displayed():
                        option = cand
                        break
                if option is not None:
                    break
            except Exception:
                pass

    if option is None:
        sb.send_keys("body", Keys.ESCAPE)
        pytest.skip("Repository picker did not show any selectable repository.")

    logger.info(f"INFO: test step - Selecting repo: {option.text}")
    try:
        option.click()
    except Exception:
        sb.execute_script("arguments[0].click();", option)
    time.sleep(2)

    sb.wait_for_element_visible("[data-slot='dialog-content'] input[name='name']", timeout=10)


def set_checkbox_near_label(sb, label_text, target_state):
    logger.info(f"INFO: test step - Setting checkbox near '{label_text}' to {target_state}")
    labels = sb.find_elements("label, span, p")
    for el in labels:
        try:
            if label_text.lower() not in (el.text or "").lower():
                continue
            container = el.find_element(By.XPATH, "./ancestor::*[.//button[@role='checkbox']][1]")
            cb = container.find_element(By.CSS_SELECTOR, "button[role='checkbox']")
            current = cb.get_attribute("aria-checked") == "true"
            if current != target_state:
                cb.click()
                time.sleep(0.4)
            return
        except Exception:
            pass


def test_schedulers_flow(sb):
    """
    8. SCHEDULERS TEST
    - Schedulers sayfasında New Scheduler modalını açar.
    - Repository popover'dan repo seçer, isim girer ve scheduler kaydeder.
    """
    logger.info("INFO: test step - Starting Schedulers E2E Test Flow")

    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")

    perform_setup_and_login(sb)
    schedulers_url = f"{base_url}/{workspace_id}/schedulers"
    sb.open(schedulers_url)
    time.sleep(4)
    dismiss_ui_blockers(sb)

    if sb.is_element_visible("div:contains('Session Expired')") or sb.is_element_visible("button:contains('Sign In')"):
        login_page = LoginPage(sb)
        login_page.api_login(base_url, os.getenv("E2E_USER_EMAIL"), os.getenv("E2E_USER_PASSWORD"))
        login_page.save_session_cookies()
        sb.open(schedulers_url)
        time.sleep(4)
        dismiss_ui_blockers(sb)

    open_new_scheduler_modal(sb)
    select_repository_from_modal(sb)

    name_input = "[data-slot='dialog-content'] input[name='name']"
    sb.wait_for_element_visible(name_input, timeout=10)
    schedule_name = f"e2e-daily-scheduler-{int(time.time())}"
    sb.type(name_input, schedule_name)

    time_input = "[data-slot='dialog-content'] input[type='time']"
    if sb.is_element_visible(time_input):
        sb.type(time_input, "02:00")

    set_checkbox_near_label(sb, "Code", True)
    set_checkbox_near_label(sb, "Pull Request", True)
    set_checkbox_near_label(sb, "Issue", True)

    save_selectors = [
        "[data-slot='dialog-footer'] button[type='submit']",
        "xpath=//div[@data-slot='dialog-footer']//button[contains(., 'Save') or contains(., 'Kaydet')]",
        "xpath=//button[@type='submit' and (contains(., 'Save') or contains(., 'Kaydet'))]",
    ]
    saved = False
    for sel in save_selectors:
        try:
            safe_click(sb, sel, timeout=5, dismiss=False)
            saved = True
            break
        except Exception:
            pass
    assert saved, "Save button could not be clicked."
    time.sleep(4)

    body = sb.get_text("body").lower()
    assert "/schedulers" in sb.get_current_url()
    assert schedule_name in body or "success" in body or "created" in body or "saved" in body
    logger.info("INFO: test step - Schedulers flow completed successfully!")
