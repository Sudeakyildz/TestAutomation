import os
import time
import logging
from selenium.webdriver.common.keys import Keys
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.waits import wait_for_page_ready, wait_for_workspace_dashboard

logger = logging.getLogger("GitsecE2E")

ADD_PROVIDER_PATHS = (
    "repositories/add",
    "repositories/github/add",
    "integrations",
    "settings/integrations",
)


def is_ci():
    """Yalnizca GitHub Actions CI kosusunu tespit eder."""
    return os.getenv("GITHUB_ACTIONS", "").lower() == "true"


def dismiss_ui_blockers(sb):
    """Tour, alert dialog ve açık modal overlay'lerini kapatır."""
    login_page = LoginPage(sb)
    login_page.bypass_onboarding()
    login_page.close_popups_if_any()

    overlay_selectors = [
        "div[data-slot='alert-dialog-overlay']",
        "div[data-slot='dialog-overlay']",
        "rect[mask*='tour-spotlight-mask']",
    ]
    for sel in overlay_selectors:
        try:
            if sb.is_element_visible(sel):
                sb.send_keys("body", Keys.ESCAPE)
                time.sleep(0.5)
        except Exception:
            pass

    dialog_close_selectors = [
        "button[aria-label='Close tour']",
        "button[aria-label='Close']",
        "//button[contains(., 'Kapat')]",
    ]
    for sel in dialog_close_selectors:
        try:
            if sb.is_element_visible(sel):
                sb.click(sel)
                time.sleep(0.5)
                break
        except Exception:
            pass

    try:
        sb.send_keys("body", Keys.ESCAPE)
    except Exception:
        pass


def safe_click(sb, selector, timeout=10, dismiss=True):
    """Overlay engellerini temizleyip normal/js click dener."""
    if dismiss:
        dismiss_ui_blockers(sb)
    sb.wait_for_element_visible(selector, timeout=timeout)
    sb.scroll_to(selector)
    time.sleep(0.3)
    try:
        sb.click(selector)
    except Exception:
        if dismiss:
            dismiss_ui_blockers(sb)
        sb.js_click(selector)
    time.sleep(0.5)


def get_switch_state(sb, switch_sel):
    """Switch durumunu aria-checked ve data-state üzerinden okur."""
    aria = sb.get_attribute(switch_sel, "aria-checked")
    data_state = sb.get_attribute(switch_sel, "data-state") or ""
    if aria == "true" or data_state in ("checked", "on", "true"):
        return True
    if aria == "false" or data_state in ("unchecked", "off", "false"):
        return False
    return None


def wait_for_switch_state(sb, switch_sel, active, timeout=60, refresh_url=None):
    """Switch durumunun güncellenmesini bekler; gerekirse sayfayı yeniler."""
    deadline = time.time() + timeout
    stable_hits = 0
    while time.time() < deadline:
        if check_license_limit_or_error(sb):
            return False
        state = get_switch_state(sb, switch_sel)
        if state is active:
            stable_hits += 1
            if stable_hits >= 2:
                break
        else:
            stable_hits = 0
        time.sleep(1)

    if refresh_url:
        logger.info("INFO: test step - Verifying switch state after page refresh...")
        sb.open(refresh_url)
        wait_for_page_ready(sb)
        scroll_table_right(sb)
        verify_deadline = time.time() + 25
        while time.time() < verify_deadline:
            if get_switch_state(sb, switch_sel) is active:
                return True
            time.sleep(1)
        return False

    return stable_hits >= 2


def click_exclude_confirm_if_any(sb):
    """Exclude onay modalındaki butonu tıklar."""
    dialog_selectors = [
        "[data-slot='alert-dialog-content']",
        "div[role='alertdialog']",
        "div[role='dialog']",
    ]
    dialog_found = False
    for sel in dialog_selectors:
        try:
            sb.wait_for_element_visible(sel, timeout=8)
            dialog_found = True
            break
        except Exception:
            pass

    if not dialog_found:
        logger.warning("WARNING: Exclude confirmation dialog did not appear.")
        return False

    confirm_selectors = [
        "[data-slot='alert-dialog-action']",
        "xpath=//button[contains(., 'Yes, Exclude')]",
        "xpath=//button[contains(., 'Hariç Tut')]",
        "xpath=//div[@role='alertdialog']//button[contains(., 'Exclude')]",
        "xpath=//div[@role='dialog']//button[contains(., 'Exclude') and not(contains(., 'Excluded'))]",
    ]
    for sel in confirm_selectors:
        try:
            if sb.is_element_visible(sel):
                safe_click(sb, sel, timeout=5, dismiss=False)
                try:
                    sb.wait_for_element_not_visible("div[role='dialog']", timeout=8)
                except Exception:
                    pass
                logger.info(f"INFO: test step - Exclude confirmed via: {sel}")
                return True
        except Exception:
            pass
    return False


def toggle_repository_switch(sb, switch_sel, target_active, page_url=None):
    """Repository switch'ini hedef duruma getirir."""
    current = get_switch_state(sb, switch_sel)
    if current is target_active:
        return True

    dismiss_ui_blockers(sb)
    sb.scroll_to(switch_sel)
    time.sleep(0.5)

    clicked = False
    for _ in range(2):
        try:
            sb.click(switch_sel)
            clicked = True
        except Exception:
            try:
                sb.js_click(switch_sel)
                clicked = True
            except Exception:
                pass
        if clicked:
            break
        time.sleep(1)

    if not target_active:
        time.sleep(1.5)
        confirmed = click_exclude_confirm_if_any(sb)
        if not confirmed:
            logger.warning("WARNING: Exclude confirm not clicked; checking if switch changed anyway.")

    if check_license_limit_or_error(sb):
        return False

    return wait_for_switch_state(sb, switch_sel, target_active, timeout=60, refresh_url=page_url)


def click_restore_submit(sb):
    """Start Restore butonuna overlay engeline takılmadan tıklar."""
    btn_selectors = [
        "xpath=//button[contains(., 'Start Restore')]",
        "xpath=//button[contains(., 'Restore') and contains(@class, 'bg-primary')]",
    ]
    for sel in btn_selectors:
        if sb.is_element_present(sel):
            safe_click(sb, sel, timeout=10)
            return True
    return False


def wait_for_restore_submitted(sb, timeout=40):
    """Restore isteğinin gönderildiğini doğrular."""
    keywords = ["submitted", "restore in progress", "queued", "started", "processing", "success"]
    sb.wait_for_condition(
        lambda: any(k in sb.get_text("body").lower() for k in keywords),
        timeout=timeout,
    )


def get_env_config():
    """Ortak URL ve workspace bilgilerini döndürür."""
    return {
        "email": os.getenv("E2E_USER_EMAIL"),
        "password": os.getenv("E2E_USER_PASSWORD"),
        "base_url": os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io"),
        "workspace_id": os.getenv("WORKSPACE_ID", "83"),
        "api_base_url": os.getenv("API_BASE_URL", "https://staging.api.gitsec.io"),
        "github_test_org": os.getenv("GITHUB_TEST_ORG", "1testhesap234-beep"),
    }


def navigate_to(sb, path_suffix, *, login=True):
    """Workspace altında bir sayfaya gider."""
    cfg = get_env_config()
    if login:
        perform_setup_and_login(sb)
    url = f"{cfg['base_url']}/{cfg['workspace_id']}/{path_suffix.lstrip('/')}"
    sb.open(url)
    wait_for_page_ready(sb)
    dismiss_ui_blockers(sb)
    return url


def assert_url_contains(sb, fragment, timeout=15):
    sb.wait_for_condition(lambda: fragment in sb.get_current_url(), timeout=timeout)


def assert_main_visible(sb, timeout=15):
    sb.assert_element("main", timeout=timeout)


def logout_via_ui(sb):
    """Kullanıcı menüsünden çıkış yapmayı dener."""
    dismiss_ui_blockers(sb)
    menu_selectors = [
        "button[data-slot='dropdown-menu-trigger']",
        "button[aria-label*='User']",
        "button[aria-label*='Account']",
        "button.rounded-full",
    ]
    for sel in menu_selectors:
        try:
            if sb.is_element_visible(sel):
                safe_click(sb, sel, timeout=5)
                time.sleep(1)
                break
        except Exception:
            pass

    logout_selectors = [
        "xpath=//button[contains(., 'Log out') or contains(., 'Logout') or contains(., 'Sign out')]",
        "xpath=//a[contains(., 'Log out') or contains(., 'Logout') or contains(., 'Sign out')]",
        "xpath=//*[@role='menuitem'][contains(., 'Log out') or contains(., 'Çıkış')]",
    ]
    for sel in logout_selectors:
        try:
            if sb.is_element_visible(sel):
                safe_click(sb, sel, timeout=5)
                time.sleep(3)
                return True
        except Exception:
            pass
    return False


def _session_needs_refresh(sb, base_url, workspace_id):
    """Oturum gecersiz veya dashboard yuklenmediyse True."""
    current_url = sb.get_current_url().lower()
    if "sign-in" in current_url:
        return True
    try:
        body = sb.get_text("body").lower()
    except Exception:
        body = ""
    if "404" in body or "not found" in body:
        return True
    if "failed to load analytics" in body:
        return True
    if sb.is_element_visible("div:contains('Session Expired')"):
        return True
    if sb.is_element_visible("button:contains('Sign In')"):
        return True
    if f"/{workspace_id}/" not in sb.get_current_url() and current_url.rstrip("/").endswith("/dashboard"):
        return True
    if not sb.is_element_visible("main"):
        return True
    return False


def open_add_provider_page(sb):
    """Add provider sayfasini bilinen route adaylari uzerinden acar."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    last_url = None
    for path in ADD_PROVIDER_PATHS:
        url = f"{cfg['base_url']}/{cfg['workspace_id']}/{path.lstrip('/')}"
        last_url = url
        sb.open(url)
        wait_for_page_ready(sb)
        dismiss_ui_blockers(sb)
        body = sb.get_text("body").lower()
        if "404" in body or "not found" in body:
            continue
        if sb.is_element_visible("main") and any(
            kw in body for kw in ("github", "bitbucket", "gitlab", "provider", "integrat")
        ):
            return url
    raise AssertionError(f"Add provider page not reachable. Last tried: {last_url}")


def perform_setup_and_login(sb):
    """Helper to perform dashboard login and return dashboard page object."""
    cfg = get_env_config()
    email = cfg["email"]
    password = cfg["password"]
    base_url = cfg["base_url"]
    workspace_id = cfg["workspace_id"]
    dashboard_url = f"{base_url}/{workspace_id}/dashboard"

    assert email, "E2E_USER_EMAIL environment variable is not defined"
    assert password, "E2E_USER_PASSWORD environment variable is not defined"

    login_page = LoginPage(sb)
    loaded = False

    if not is_ci():
        loaded = login_page.load_session_cookies(base_url)
        if loaded:
            logger.info("INFO: test step - Reusing existing session cookies to bypass login")
            sb.open(dashboard_url)
            wait_for_page_ready(sb)
            if _session_needs_refresh(sb, base_url, workspace_id):
                logger.info("INFO: test step - Session expired or invalid. Re-authenticating...")
                loaded = False

    if not loaded:
        logger.info("INFO: test step - No valid cookies found, doing full login / API bypass")
        loaded = login_page.api_login(base_url, email, password)
        if loaded:
            sb.open(dashboard_url)
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

    if _session_needs_refresh(sb, base_url, workspace_id):
        logger.info("INFO: test step - Dashboard still invalid after login; retrying API login once")
        if login_page.api_login(base_url, email, password):
            sb.open(dashboard_url)
            wait_for_page_ready(sb)

    try:
        wait_for_workspace_dashboard(sb, workspace_id, timeout=25)
    except Exception as e:
        logger.error(f"ERROR: Dashboard loading check failed: {str(e)}")
        sb.open(dashboard_url)
        wait_for_workspace_dashboard(sb, workspace_id, timeout=25)

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
    except Exception:
        pass
    return False
