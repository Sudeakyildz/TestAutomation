import time
import re
import os
import logging
from datetime import datetime, timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.login_page import BasePage
from utils.github_email_otp import poll_github_otp

logger = logging.getLogger("GitsecE2E")

class GithubLoginPage(BasePage):
    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, 'input[name="login"]')
    PASSWORD_INPUT = (By.CSS_SELECTOR, 'input[name="password"]')
    SIGN_IN_BUTTON = (By.CSS_SELECTOR, 'input[name="commit"]')
    
    # OTP / 2FA Inputs
    SUDO_EMAIL_OTP_INPUT = (By.CSS_SELECTOR, '#sudo_email_otp, input[name="sudo_email_otp"]')
    LOGIN_OTP_INPUT = (By.CSS_SELECTOR, '#otp, input[name="otp"]')
    DEVICE_CODE_INPUT = (By.CSS_SELECTOR, '#otp, input[name="otp"], input[name="verification_key"], input[autocomplete="one-time-code"]')
    
    # Sudo triggers
    SUDO_SEND_EMAIL_BTN = (By.CSS_SELECTOR, '#sudo-send-email')
    
    # Install & Authorize Buttons
    AUTHORIZE_BUTTON = (By.CSS_SELECTOR, 'button[name="authorize"]')

    def find_optional_element(self, locator):
        """Finds an element without triggering implicit waits."""
        sel = locator[1] if isinstance(locator, tuple) else locator
        if self.sb.is_element_present(sel):
            return self.sb.find_element(sel)
        return None

    def find_optional_element_by_xpath(self, xpath):
        """Finds an element by XPath without triggering implicit waits."""
        if self.sb.is_element_present(xpath):
            return self.sb.find_element(xpath)
        return None

    def is_popup_closed(self):
        try:
            return len(self.sb.driver.window_handles) <= 1
        except:
            return True

    def get_active_otp_input(self):
        selectors = [
            self.SUDO_EMAIL_OTP_INPUT,
            self.LOGIN_OTP_INPUT,
            self.DEVICE_CODE_INPUT
        ]
        for sel in selectors:
            el = self.find_optional_element(sel)
            if el:
                return el
        return None

    def get_send_code_via_email_button(self):
        buttons = self.sb.find_elements("button")
        for btn in buttons:
            try:
                text = btn.text.lower()
                if "via email" in text or "send a code" in text or "verify via email" in text:
                    return btn
            except:
                pass
        return None

    def is_two_factor_screen_visible(self):
        if self.is_popup_closed():
            return False
        try:
            url = self.sb.get_current_url()
            if "two-factor" in url or "verify" in url:
                return True
            
            body_text = self.sb.get_text("body").lower()
            heading = any(k in body_text for k in ["two-factor", "two-step", "authentication code", "confirm access"])
            otp_visible = self.get_active_otp_input() is not None
            return heading or otp_visible
        except:
            return False

    def is_sudo_ui_visible(self):
        if self.is_popup_closed():
            return False
        otp = self.find_optional_element(self.SUDO_EMAIL_OTP_INPUT) is not None
        send = self.find_optional_element(self.SUDO_SEND_EMAIL_BTN) is not None
        send_code_email = self.get_send_code_via_email_button() is not None
        return otp or send or send_code_email

    def login(self, username, password):
        logger.info(f"INFO: test step - Logging into GitHub as: {username}")
        self.safeType(self.USERNAME_INPUT, username)
        self.safeType(self.PASSWORD_INPUT, password)
        self.safeClick(self.SIGN_IN_BUTTON)
        time.sleep(2)

    def try_click_send_code_via_email(self):
        try:
            body_text = self.sb.get_text("body").lower()
            if re.search(r"device verification|we sent a (?:verification )?code to|sent an email with a", body_text, re.IGNORECASE):
                logger.info("INFO: test step - Code already sent automatically (Device Verification).")
                return False
        except:
            pass

        btn = self.get_send_code_via_email_button()
        if btn:
            try:
                btn.click()
                logger.info("INFO: test step - Clicked Send code via email button")
                return True
            except:
                try:
                    self.sb.js_click(btn)
                    logger.info("INFO: test step - Clicked Send code via email button via JS fallback")
                    return True
                except:
                    pass

        send_btn = self.find_optional_element(self.SUDO_SEND_EMAIL_BTN)
        if send_btn:
            try:
                send_btn.click()
                logger.info("INFO: test step - Clicked sudo send email button")
                return True
            except:
                pass

        return False

    def enter_verification_code(self, code):
        otp_field = self.get_active_otp_input()
        if otp_field:
            otp_field.click()
            otp_field.clear()
            for char in code:
                otp_field.send_keys(char)
                time.sleep(0.05)
            logger.info(f"INFO: test step - Verification code typed successfully")

    def submit_sudo_email_otp(self):
        otp_field = self.get_active_otp_input()
        if otp_field:
            try:
                form = self.sb.find_element(otp_field).find_element(By.XPATH, "./ancestor::form")
                submit_btn = form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                self.sb.click(submit_btn)
                logger.info("INFO: test step - Submitted Sudo OTP form click")
                return
            except:
                try:
                    buttons = self.sb.find_elements("button")
                    verify_btn = next((b for b in buttons if "verify" in b.text.lower()), None)
                    if verify_btn:
                        self.sb.click(verify_btn)
                        logger.info("INFO: test step - Clicked verify button")
                        return
                    else:
                        raise Exception("Verify button not found by text")
                except:
                    otp_field.send_keys("\n")
                    logger.info("INFO: test step - Pressed Enter on OTP field")

    def handle_two_factor_authentication(self, pre_login_time=None):
        logger.info("INFO: test step - Waiting for page transition after sign-in...")
        transition_deadline = time.time() + 15
        while time.time() < transition_deadline:
            try:
                url = self.sb.get_current_url()
                if "login" not in url and "session" not in url:
                    break
            except Exception:
                pass
            time.sleep(0.5)
            
        time.sleep(2)
        if not self.is_two_factor_screen_visible():
            logger.info("INFO: test step - No GitHub 2FA screen detected.")
            return True

        logger.info("INFO: test step - GitHub 2FA challenge detected!")
        
        has_mail = bool(os.getenv("GITHUB_MAIL_USER")) and bool(os.getenv("GITHUB_MAIL_PASSWORD"))
        if not has_mail:
            logger.error("ERROR: GITHUB_MAIL_USER and GITHUB_MAIL_PASSWORD are not set in .env. Cannot auto-complete 2FA.")
            return False

        self.try_click_send_code_via_email()
        time.sleep(5)
        
        try:
            code = poll_github_otp(min_received_at=pre_login_time)
            self.enter_verification_code(code)
            self.submit_sudo_email_otp()
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"ERROR: GitHub 2FA mail polling failed: {str(e)}")
            return False

    def find_install_authorize_button_selector(self):
        selectors = [
            "button.js-integrations-install-form-submit",
            "button:contains('Install & Authorize')",
            "button:contains('Install and Authorize')",
            "button:contains('Install')",
            "button[type='submit']"
        ]
        for sel in selectors:
            if self.sb.is_element_present(sel):
                try:
                    txt = self.sb.get_text(sel).lower()
                    if "install" in txt or "authorize" in txt:
                        return sel
                except:
                    pass
        return None

    def click_install_and_authorize(self, selector=None):
        if not selector:
            selector = self.find_install_authorize_button_selector()
        if selector:
            try:
                self.sb.scroll_to(selector)
                time.sleep(0.5)
                self.sb.click(selector)
                logger.info(f"INFO: test step - Clicked Install & Authorize button using selector: {selector}")
                return True
            except Exception as e1:
                logger.warning(f"WARNING: Standard click on Install & Authorize button failed: {e1}")
                try:
                    self.sb.js_click(selector)
                    logger.info(f"INFO: test step - Clicked Install & Authorize button via JS using selector: {selector}")
                    return True
                except Exception as e2:
                    logger.error(f"ERROR: JS click on Install & Authorize button failed: {e2}")
        return False

    def handle_sudo_prompt_if_any(self):
        password_field = self.find_optional_element((By.CSS_SELECTOR, 'input[name="password"]'))
        username_field = self.find_optional_element(self.USERNAME_INPUT)
        if password_field and not username_field:
            logger.info("INFO: test step - Sudo password verification prompt detected.")
            password = os.getenv("GITHUB_TEST_PASSWORD", "")
            if password:
                password_field.send_keys(password)
                confirm_btn = self.find_optional_element((By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'))
                if confirm_btn:
                    confirm_btn.click()
                    logger.info("INFO: test step - Sudo password submitted.")
                    time.sleep(3)

        if self.is_sudo_ui_visible():
            logger.info("INFO: test step - Sudo OTP verification prompt detected.")
            sent_at = datetime.now(timezone.utc)
            self.try_click_send_code_via_email()
            time.sleep(5)
            try:
                code = poll_github_otp(min_received_at=sent_at)
                self.enter_verification_code(code)
                self.submit_sudo_email_otp()
                time.sleep(3)
            except Exception as e:
                logger.error(f"ERROR: GitHub Sudo OTP verification failed: {str(e)}")

    def complete_permissions_install_flow(self):
        logger.info("INFO: test step - Starting installation permission flow...")
        sel = None
        start_wait = time.time()
        while time.time() - start_wait < 15:
            if self.is_popup_closed():
                logger.info("INFO: test step - Popup closed early. Exiting flow.")
                return
            sel = self.find_install_authorize_button_selector()
            if sel:
                break
            time.sleep(0.5)
            
        if sel:
            self.click_install_and_authorize(sel)
        else:
            logger.warning("WARNING: Install & Authorize button not found within 15 seconds")
            
        time.sleep(3)
        if self.is_popup_closed():
            logger.info("INFO: test step - Popup closed after click. Exiting install flow.")
            return
            
        self.handle_sudo_prompt_if_any()
        time.sleep(3)
        
        if self.is_popup_closed():
            logger.info("INFO: test step - Popup closed after sudo check. Exiting install flow.")
            return
            
        sel_after_sudo = None
        start_wait_after = time.time()
        while time.time() - start_wait_after < 5:
            if self.is_popup_closed():
                return
            sel_after_sudo = self.find_install_authorize_button_selector()
            if sel_after_sudo:
                break
            time.sleep(0.5)
            
        if sel_after_sudo:
            logger.info("INFO: test step - Re-clicking Install & Authorize button after sudo authorization")
            self.click_install_and_authorize(sel_after_sudo)
            time.sleep(3)

    def authorize_app(self):
        try:
            authorize_btn = self.find_optional_element(self.AUTHORIZE_BUTTON)
            if authorize_btn:
                self.sb.scroll_to(authorize_btn)
                time.sleep(0.5)
                authorize_btn.click()
                logger.info("INFO: test step - Clicked Authorize App button")
            else:
                logger.info("INFO: test step - Authorize app button not displayed or already authorized.")
        except:
            pass


