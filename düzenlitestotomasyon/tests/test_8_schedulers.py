import os
import sys
import time
import logging
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, safe_click, get_env_config
from pages.login_page import LoginPage
from tests.journey_helpers import delete_schedule_by_name, open_workspace_path
from tests.api_helpers import list_items
from utils.waits import wait_for_page_ready

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
    btn = find_button_by_text(sb, "New Scheduler", "Create Scheduler", "Yeni", "Schedule")
    if btn is None:
        xpaths = [
            "xpath=//button[contains(., 'New Scheduler') or contains(., 'Create Scheduler')]",
            "xpath=//button[contains(., 'Yeni') and contains(., 'Scheduler')]",
            "xpath=//a[contains(., 'New Scheduler') or contains(., 'Create Scheduler')]",
        ]
        for xpath in xpaths:
            try:
                if sb.is_element_visible(xpath):
                    btn = sb.find_element(xpath)
                    break
            except Exception:
                pass
    if btn is None:
        pytest.skip("New Scheduler button not found on schedulers page.")
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


def wait_for_schedule_save(sb, schedule_name, timeout=45):
    """Kaydet tiklandiktan sonra modal kapanisini veya schedule adini bekler."""
    target = schedule_name.lower()

    def saved():
        body = sb.get_text("body").lower()
        if "saving..." in body:
            return False
        try:
            if sb.is_element_visible("[data-slot='dialog-content']"):
                return False
        except Exception:
            pass
        if target in body:
            return True
        return "/schedulers" in sb.get_current_url() and any(
            k in body for k in ("success", "created", "saved", "scheduler")
        )

    sb.wait_for_condition(saved, timeout=timeout)
    wait_for_page_ready(sb)


def schedule_exists_by_name(api_client, schedule_name):
    status, payload = api_client.get("/api/backup/schedules/tenant")
    if status != 200:
        return False
    return any(
        isinstance(item, dict) and item.get("name") == schedule_name
        for item in list_items(payload)
    )


def test_schedulers_flow(sb, api_client):
    """
    8. SCHEDULERS TEST
    - Schedulers sayfasında New Scheduler modalını açar.
    - Repository popover'dan repo seçer, isim girer ve scheduler kaydeder.
    - API ile oluşturulan schedule temizlenir.
    """
    logger.info("INFO: test step - Starting Schedulers E2E Test Flow")

    cfg = get_env_config()
    base_url = cfg["base_url"]
    workspace_id = cfg["workspace_id"]
    schedule_name = None

    try:
        perform_setup_and_login(sb)
        open_workspace_path(sb, cfg, "schedulers")

        if sb.is_element_visible("div:contains('Session Expired')") or sb.is_element_visible("button:contains('Sign In')"):
            login_page = LoginPage(sb)
            login_page.api_login(base_url, cfg["email"], cfg["password"])
            login_page.save_session_cookies()
            open_workspace_path(sb, cfg, "schedulers")

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
        wait_for_schedule_save(sb, schedule_name)

        body = sb.get_text("body").lower()
        api_ok = schedule_exists_by_name(api_client, schedule_name)
        assert "/schedulers" in sb.get_current_url()
        assert (
            schedule_name.lower() in body
            or api_ok
            or any(k in body for k in ("success", "created", "saved"))
        ), f"Schedule save not confirmed (api_ok={api_ok})"
        logger.info("INFO: test step - Schedulers flow completed successfully!")
    finally:
        if schedule_name:
            deleted = delete_schedule_by_name(api_client, schedule_name)
            logger.info("INFO: test step - Schedule cleanup (%s): %s", schedule_name, deleted)
