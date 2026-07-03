import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger("GitsecE2E")

class BasePage:
    def __init__(self, sb):
        self.sb = sb

    def waitForVisible(self, locator, timeout=10):
        logger.info("INFO: test step - Waiting for element visibility")
        logger.debug(f"DEBUG: locator info - {locator}")
        sel = locator[1] if isinstance(locator, tuple) else locator
        if isinstance(locator, tuple) and locator[0] == By.XPATH and not sel.startswith("xpath="):
            sel = f"xpath={sel}"
        self.sb.wait_for_element_visible(sel, timeout=timeout)
        return self.sb.find_element(sel)
 
    def safeClick(self, locator, timeout=10):
        logger.info("INFO: test step - Clicking element")
        logger.debug(f"DEBUG: locator info - {locator}")
        sel = locator[1] if isinstance(locator, tuple) else locator
        if isinstance(locator, tuple) and locator[0] == By.XPATH and not sel.startswith("xpath="):
            sel = f"xpath={sel}"
        self.sb.click(sel, timeout=timeout)
 
    def safeType(self, locator, text, timeout=10):
        logger.info("INFO: test step - Typing text into element")
        logger.debug(f"DEBUG: locator info - {locator}")
        sel = locator[1] if isinstance(locator, tuple) else locator
        if isinstance(locator, tuple) and locator[0] == By.XPATH and not sel.startswith("xpath="):
            sel = f"xpath={sel}"
        self.sb.type(sel, text, timeout=timeout)

    def dismiss_open_menus(self):
        logger.info("INFO: test step - Dismissing any open menus via Escape key")
        try:
            self.sb.send_keys("body", Keys.ESCAPE)
        except Exception as e:
            logger.debug(f"DEBUG: Failed to dismiss open menus: {str(e)}")

    def bypass_onboarding(self):
        logger.info("INFO: test step - Injecting tour skip into localStorage")
        tour_value = '{"state":{"completedTours":{"onboarding":5}},"version":0}'
        try:
            self.sb.set_local_storage_item("gs-tour", tour_value)
        except Exception as e:
            logger.debug(f"DEBUG: failed to inject localStorage bypass: {str(e)}")

    def close_popups_if_any(self):
        logger.info("INFO: test step - Scanning for optional popups (KEP or onboarding guides)")
        try:
            if self.sb.is_element_visible("rect[mask*='tour-spotlight-mask']"):
                logger.info("INFO: test step - Spotlight mask detected. Removing element from DOM directly to bypass onboarding.")
                self.bypass_onboarding()
                self.sb.remove_element("rect[mask*='tour-spotlight-mask']")
        except Exception as e:
            logger.debug(f"DEBUG: Spotlight mask removal failed: {str(e)}")
        
        try:
            if self.sb.is_element_visible("button[aria-label='Close tour']"):
                self.sb.click("button[aria-label='Close tour']")
                logger.info("INFO: test step - Closed onboarding tour modal successfully")
        except Exception as e:
            logger.debug(f"DEBUG: Failed to close onboarding tour modal: {str(e)}")

        try:
            self.sb.send_keys("body", Keys.ESCAPE)
        except:
            pass

        try:
            kep_close_btn = "//button[contains(text(), 'Kapat') or contains(text(), 'Close') or @aria-label='Close']"
            if self.sb.is_element_visible(kep_close_btn):
                self.sb.click(kep_close_btn)
                logger.info("INFO: test step - Closed an optional overlay popup successfully")
        except Exception as e:
            logger.debug(f"DEBUG: locator info - no optional popups to click: {str(e)}")




class LoginPage(BasePage):
    # Locators
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password'], input[type='password']")
    SIGN_IN_BUTTON = (By.XPATH, "//button[contains(translate(., 'SIGN IN', 'sign in'), 'sign in')]")
    
    # Captcha Elements
    CF_TURNSTILE_IFRAME = "iframe[src*='challenges.cloudflare.com']"
    RECAPTCHA_ANCHOR_IFRAME = "iframe[src*='google.com/recaptcha/api2/anchor']"
    RECAPTCHA_CHALLENGE_IFRAME = "iframe[src*='google.com/recaptcha/api2/bframe']"
    
    # Optional Popups
    KEP_CLOSE_BTN = (By.XPATH, "//button[contains(text(), 'Kapat') or contains(text(), 'Close') or @aria-label='Close']")

    def navigate_to_login(self, base_url):
        url = f"{base_url}/sign-in"
        logger.info(f"INFO: test step - Navigating to login page: {url}")
        self.sb.open(url)
        self.bypass_onboarding()

    def handle_captcha(self, timeout=5):
        logger.info("INFO: test step - Checking for Captcha overlays...")
        captcha_map = {
            "Cloudflare Turnstile": self.CF_TURNSTILE_IFRAME,
            "Google reCAPTCHA Anchor": self.RECAPTCHA_ANCHOR_IFRAME,
            "Google reCAPTCHA Challenge": self.RECAPTCHA_CHALLENGE_IFRAME
        }
        for _ in range(int(timeout / 0.5)):
            for name, selector in captcha_map.items():
                if self.sb.is_element_visible(selector):
                    logger.warning(f"CAPTCHA detected: {name}. Bypassing using API login...")
                    return True
            time.sleep(0.5)
        logger.info("INFO: test step - No active Captcha overlay detected.")
        return False

    def api_login(self, base_url, email, password):
        api_base_url = os.getenv("API_BASE_URL", "https://staging.api.gitsec.io")
        logger.info(f"INFO: test step - Performing API login to bypass CAPTCHA. API URL: {api_base_url}")
        for attempt in range(3):
            try:
                import urllib.request
                import urllib.error
                import json
                
                url = f"{api_base_url}/auth/signin"
                data = json.dumps({"email": email, "password": password}).encode("utf-8")
                req = urllib.request.Request(
                    url, 
                    data=data, 
                    headers={"Content-Type": "application/json"}
                )
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    token = resp_data.get("data", {}).get("token")
                    if token:
                        logger.info("INFO: test step - API login successful! Token retrieved.")
                        self.sb.open(base_url)
                        self.sb.delete_all_cookies()
                        cookie = {
                            "name": "gs_token",
                            "value": token,
                            "domain": ".gitsec.io",
                            "path": "/",
                            "secure": True,
                            "sameSite": "Lax"
                        }
                        self.sb.add_cookie(cookie)
                        logger.info("INFO: test step - API token cookie injected into browser session.")
                        self.bypass_onboarding()
                        
                        workspace_id = os.getenv("WORKSPACE_ID", "83")
                        self.sb.open(f"{base_url}/{workspace_id}/dashboard")
                        self.save_session_cookies()
                        return True
                    else:
                        logger.error("ERROR: API login response did not contain token")
            except Exception as e:
                backoff = 2 ** attempt
                logger.error(f"ERROR: API login request failed on attempt {attempt + 1}/3: {str(e)}")
                if attempt < 2:
                    logger.info(f"Retrying API login in {backoff} seconds...")
                    time.sleep(backoff)
        return False

    def login(self, email, password):
        base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
        if self.handle_captcha(timeout=3):
            logger.info("INFO: test step - Captcha detected on login page load. Falling back to API login bypass.")
            if self.api_login(base_url, email, password):
                return
            logger.error("ERROR: API login bypass failed after load captcha detection.")
        
        self.sb.type(self.EMAIL_INPUT[1], email)
        self.sb.type(self.PASSWORD_INPUT[1], password)
        self.sb.click(self.SIGN_IN_BUTTON[1])
        
        if self.handle_captcha(timeout=5):
            logger.info("INFO: test step - Captcha detected after credentials submission. Falling back to API login bypass.")
            if self.api_login(base_url, email, password):
                return
            logger.error("ERROR: API login bypass failed after submit captcha detection.")
        time.sleep(3)
        
    def save_session_cookies(self):
        cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session_cookies.json")
        logger.info(f"INFO: test step - Saving session cookies to {cookie_file}")
        try:
            cookies = self.sb.get_cookies()
            import json
            with open(cookie_file, "w") as f:
                json.dump(cookies, f)
            logger.info("INFO: test step - Cookies saved successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to save cookies: {str(e)}")

    def load_session_cookies(self, base_url):
        cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "session_cookies.json")
        loaded_file = False
        if os.path.exists(cookie_file):
            logger.info(f"INFO: test step - Loading session cookies from {cookie_file}")
            try:
                import json
                with open(cookie_file, "r") as f:
                    cookies = json.load(f)
                
                self.sb.open(base_url)
                self.sb.delete_all_cookies()
                
                for cookie in cookies:
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    try:
                        self.sb.add_cookie(cookie)
                    except Exception as e:
                        pass
                
                logger.info("INFO: test step - Session cookies loaded successfully")
                self.bypass_onboarding()
                loaded_file = True
            except Exception as e:
                logger.error(f"ERROR: Failed to load session cookies: {str(e)}")
        
        if not loaded_file:
            logger.info("INFO: test step - Cookie file loading failed or missing. Bypassing using direct API login...")
            email = os.getenv("E2E_USER_EMAIL")
            password = os.getenv("E2E_USER_PASSWORD")
            if email and password:
                loaded_file = self.api_login(base_url, email, password)
                
        return loaded_file



