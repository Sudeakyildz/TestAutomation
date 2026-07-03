import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from pages.login_page import BasePage

logger = logging.getLogger("GitsecE2E")

class DashboardPage(BasePage):
    # --- Locators ---
    REPOSITORIES_CARD = (By.CSS_SELECTOR, "a[href*='/repositories']")
    BACKUPS_CARD = (By.CSS_SELECTOR, "a[href*='/backups']")
    STORAGE_CARD = (By.CSS_SELECTOR, "a[href*='/storage']")
    
    # Top Bar elements
    HELP_BUTTON = (By.CSS_SELECTOR, "button.cursor-help, button[aria-label*='Tour']")
    SEARCH_SIDE_BUTTON = (By.CSS_SELECTOR, "button[aria-label*='Search'], button[class*='search']")
    SIDEBAR_TOGGLE_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Toggle Sidebar']")


    def return_to_dashboard(self, base_url, workspace_id):
        url = f"{base_url}/{workspace_id}/dashboard"
        logger.info(f"INFO: test step - Navigating back to dashboard via explicit URL: {url}")
        self.sb.open(url)
        self.bypass_onboarding()
        self.close_popups_if_any()

    def navigate_to_repositories(self):
        logger.info("INFO: test step - Clicking Repositories card")
        self.safeClick(self.REPOSITORIES_CARD, timeout=30)
        time.sleep(2)

    def navigate_to_backups(self):
        logger.info("INFO: test step - Clicking Backups card")
        self.safeClick(self.BACKUPS_CARD, timeout=30)
        time.sleep(2)

    def navigate_to_storage(self):
        logger.info("INFO: test step - Clicking Storage size card")
        self.safeClick(self.STORAGE_CARD, timeout=30)
        time.sleep(2)

    def navigate_to_active_tasks_view_all(self):
        logger.info("INFO: test step - Clicking Active Tasks View All")
        self.sb.wait_for_element_present("a[href*='/activity']", timeout=30)
        self.sb.scroll_to("a[href*='/activity']")
        time.sleep(1)
        links = self.sb.find_elements("a[href*='/activity']")
        if len(links) >= 1:
            links[0].click()
        else:
            raise Exception("Active Tasks View All link not found")
        time.sleep(2)

    def navigate_to_recently_completed_view_all(self):
        logger.info("INFO: test step - Clicking Recently Completed View All")
        self.sb.wait_for_element_present("a[href*='/activity']", timeout=30)
        self.sb.scroll_to("a[href*='/activity']")
        time.sleep(1)
        links = self.sb.find_elements("a[href*='/activity']")
        if len(links) >= 2:
            links[1].click()
        else:
            raise Exception("Recently Completed View All link not found")
        time.sleep(2)

    def navigate_to_premium(self):
        logger.info("INFO: test step - Clicking Premium button")
        selector = "button:contains('Premium'), a:contains('Premium'), button:contains('Upgrade'), a:contains('Upgrade'), a[href*='billing']"
        try:
            self.sb.wait_for_element_visible(selector, timeout=15)
            self.sb.click(selector)
            logger.info("INFO: test step - Clicked Premium/Upgrade/Billing button successfully.")
        except Exception as e:
            logger.warning(f"WARNING: Premium button not found via standard selector: {e}. Trying fallback...")
            elements = self.sb.find_elements("button, a")
            btn = None
            for el in elements:
                try:
                    txt = el.text.lower()
                    href = el.get_attribute("href") or ""
                    if "premium" in txt or "freemium" in txt or "upgrade" in txt or "premium" in href or "upgrade" in href:
                        btn = el
                        break
                except:
                    pass
            if btn:
                btn.click()
            else:
                raise Exception("Premium/Upgrade button not found in fallback search either")
        time.sleep(2)

    def click_help(self):
        logger.info("INFO: test step - Clicking Help (Take a Tour) button")
        self.safeClick(self.HELP_BUTTON, timeout=30)
        time.sleep(2)

    def find_language_button(self):
        buttons = self.sb.find_elements("button")
        for btn in buttons:
            try:
                html = btn.get_attribute("innerHTML") or ""
                if "languages" in html or "lucide-languages" in html:
                    return btn
            except:
                pass
        return None

    def change_language_to_tr(self):
        logger.info("INFO: test step - Switching language to Turkish (TR)")
        btn = self.find_language_button()
        if btn:
            btn.click()
            time.sleep(1)
            items = self.sb.find_elements("[role='menuitem'], [class*='menuitem'], button, a")
            tr_item = None
            for item in items:
                try:
                    txt = item.text.lower()
                    if "türkçe" in txt or "tr" == txt or "tr" in txt.split():
                        tr_item = item
                        break
                except:
                    pass
            if tr_item:
                tr_item.click()
            else:
                raise Exception("Turkish menu item not found")
        else:
            logger.warning("WARNING: Language switcher button not found. Skipping language switch to TR.")
            return False
        self.dismiss_open_menus()
        time.sleep(2)
        return True

    def change_language_to_en(self):
        logger.info("INFO: test step - Switching language to English (EN)")
        btn = self.find_language_button()
        if btn:
            btn.click()
            time.sleep(1)
            items = self.sb.find_elements("[role='menuitem'], [class*='menuitem'], button, a")
            en_item = None
            for item in items:
                try:
                    txt = item.text.lower()
                    if "english" in txt or "en" == txt or "en" in txt.split():
                        en_item = item
                        break
                except:
                    pass
            if en_item:
                en_item.click()
            else:
                raise Exception("English menu item not found")
        else:
            logger.warning("WARNING: Language switcher button not found. Skipping language switch to EN.")
            return False
        self.dismiss_open_menus()
        time.sleep(2)
        return True

    def find_theme_button(self):
        buttons = self.sb.find_elements("button")
        for btn in buttons:
            try:
                html = btn.get_attribute("innerHTML") or ""
                if any(k in html for k in ["lucide-moon", "lucide-sun", "lucide-monitor", "lucide-laptop", "moon", "sun", "monitor", "laptop"]):
                    return btn
            except:
                pass
        return None

    def select_theme_light(self):
        logger.info("INFO: test step - Selecting Light theme")
        btn = self.find_theme_button()
        if btn:
            btn.click()
            time.sleep(1)
            items = self.sb.find_elements("[role='menuitem'], button, a")
            light_item = next((i for i in items if "light" in i.text.lower() or "açık" in i.text.lower()), None)
            if light_item:
                light_item.click()
            else:
                raise Exception("Light theme option not found")
        else:
            raise Exception("Theme toggle button not found")
        self.dismiss_open_menus()
        time.sleep(2)

    def select_theme_system(self):
        logger.info("INFO: test step - Selecting System theme")
        btn = self.find_theme_button()
        if btn:
            btn.click()
            time.sleep(1)
            items = self.sb.find_elements("[role='menuitem'], button, a")
            system_item = next((i for i in items if "system" in i.text.lower() or "sistem" in i.text.lower()), None)
            if system_item:
                system_item.click()
            else:
                raise Exception("System theme option not found")
        else:
            raise Exception("Theme toggle button not found")
        self.dismiss_open_menus()
        time.sleep(2)

    def select_theme_dark(self):
        logger.info("INFO: test step - Selecting Dark theme")
        btn = self.find_theme_button()
        if btn:
            btn.click()
            time.sleep(1)
            items = self.sb.find_elements("[role='menuitem'], button, a")
            dark_item = next((i for i in items if "dark" in i.text.lower() or "koyu" in i.text.lower()), None)
            if dark_item:
                dark_item.click()
            else:
                raise Exception("Dark theme option not found")
        else:
            raise Exception("Theme toggle button not found")
        self.dismiss_open_menus()
        time.sleep(2)

    def click_search_side_button(self):
        logger.info("INFO: test step - Clicking Search side button")
        desktop_sel = "input[placeholder*='Search'], div[cmdk-root] input"
        mobile_sel = "button[aria-label*='Search']"
        if self.sb.is_element_visible(desktop_sel):
            self.sb.click(desktop_sel)
        else:
            self.sb.wait_for_element_visible(mobile_sel, timeout=15)
            self.sb.click(mobile_sel)
        time.sleep(1)

    def click_sidebar_toggle(self):
        logger.info("INFO: test step - Clicking Sidebar toggle button")
        self.safeClick(self.SIDEBAR_TOGGLE_BUTTON, timeout=30)
        time.sleep(1)
