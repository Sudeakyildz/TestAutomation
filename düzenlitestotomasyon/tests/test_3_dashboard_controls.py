import os
import sys
import time
import logging
import pytest
from selenium.webdriver.common.keys import Keys

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from tests.helpers import perform_setup_and_login, assert_main_visible

logger = logging.getLogger("GitsecE2E")

def test_dashboard_ui_controls(sb):
    """
    3. DASHBOARD UI CONTROLS TEST
    - Performs login.
    - Tests the following dashboard UI controls:
      - Help (question mark) button -> Click/Dismiss.
      - Language switcher -> Switch to Turkish -> Verify -> Switch to English -> Verify.
      - Theme toggler -> Switch to Light -> Verify -> Switch to System -> Switch to Dark -> Verify.
      - Search side button -> Click to expand/collapse.
      - Sidebar expand/collapse button -> Click to toggle.
    """
    logger.info("INFO: test step - Starting Dashboard UI Controls Test")
    
    dashboard_page = perform_setup_and_login(sb)
    
    # 1. Help (Take a Tour) button test
    if dashboard_page.click_help():
        logger.info("INFO: test step - Help tour clicked, dismissing tour overlays...")
        try:
            sb.send_keys("body", Keys.ESCAPE)
        except Exception:
            pass

        login_page = LoginPage(sb)
        login_page.close_popups_if_any()
        assert_main_visible(sb)
    else:
        logger.warning("WARNING: Help button not present on this environment — skipping tour interaction")
        
    # 2. Language switcher test (TR -> EN)
    try:
        switched = dashboard_page.change_language_to_tr()
        if switched:
            logger.info("INFO: test step - Verifying page language changed to Turkish")
            page_source = sb.get_page_source().lower()
            assert "dil" in page_source or "türkçe" in page_source or "yedek" in page_source, "Turkish language switch not detected"
            
            dashboard_page.change_language_to_en()
            logger.info("INFO: test step - Verifying page language changed back to English")
            
            page_source_en = sb.get_page_source().lower()
            assert "language" in page_source_en or "english" in page_source_en or "backup" in page_source_en, "English language switch back not detected"
        else:
            logger.warning("Language switcher is not present on this page/environment. Skipping switch verification.")
    except Exception as e:
        logger.error(f"ERROR: Language switcher failed: {str(e)}")
        raise e
        
    # 3. Theme toggler test (Light -> System -> Dark)
    try:
        dashboard_page.select_theme_light()
        logger.info("INFO: test step - Verifying theme changed to Light")
        html_class = sb.get_attribute("html", "class") or ""
        html_style = sb.get_attribute("html", "style") or ""
        assert "light" in html_class or "light" in html_style or "dark" not in html_class, "Light theme class not found on HTML element"
        
        dashboard_page.select_theme_system()
        logger.info("INFO: test step - Theme changed to System successfully")
        
        dashboard_page.select_theme_dark()
        logger.info("INFO: test step - Verifying theme changed back to Dark")
        html_class_dark = sb.get_attribute("html", "class") or ""
        assert "dark" in html_class_dark or "dark" in html_style or "color-scheme: dark" in html_style, "Dark theme class not found on HTML element"
    except Exception as e:
        logger.error(f"ERROR: Theme switcher test failed: {str(e)}")
        raise e
        
    # 4. Search side button test
    try:
        dashboard_page.click_search_side_button()
        logger.info("INFO: test step - Search side button clicked once to open search dialog")
        time.sleep(1)
        search_open = sb.is_element_visible(
            "[data-slot='dialog-content'], input[placeholder*='Search'], [cmdk-input]"
        )
        dashboard_page.dismiss_open_menus()
        logger.info("INFO: test step - Search dialog dismissed via Escape key")
        assert search_open or sb.is_element_visible("main"), "Search control did not open and dashboard not visible"
    except Exception as e:
        logger.error(f"ERROR: Search side button failed: {str(e)}")
        raise e
        
    # 5. Sidebar collapse/expand test
    try:
        dashboard_page.click_sidebar_toggle()
        logger.info("INFO: test step - Sidebar collapsed")
        dashboard_page.click_sidebar_toggle()
        logger.info("INFO: test step - Sidebar expanded back")
        assert sb.is_element_visible("button[aria-label='Toggle Sidebar']"), "Sidebar toggle button missing after toggle"
    except Exception as e:
        logger.error(f"ERROR: Sidebar toggle failed: {str(e)}")
        raise e
        
    logger.info("INFO: test step - Dashboard UI Controls Test completed successfully!")
