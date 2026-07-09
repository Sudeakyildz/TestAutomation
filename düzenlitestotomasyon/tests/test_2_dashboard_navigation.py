import os
import sys
import time
import logging
import pytest

# Adjust path to ensure POM imports work regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from tests.helpers import perform_setup_and_login, get_env_config
from utils.waits import wait_for_page_ready

logger = logging.getLogger("GitsecE2E")


def _wait_for_url_or_content(sb, url_fragments, content_keywords, timeout=20):
    """URL veya sayfa icerigi ile yuklenmeyi dogrular."""
    def loaded():
        url = sb.get_current_url().lower()
        if any(fragment in url for fragment in url_fragments):
            return True
        try:
            if not sb.is_element_visible("main"):
                return False
            body = sb.get_text("body").lower()
            return any(keyword in body for keyword in content_keywords)
        except Exception:
            return False

    sb.wait_for_condition(loaded, timeout=timeout)
    wait_for_page_ready(sb)

def test_dashboard_navigation_flow(sb):
    """
    2. DASHBOARD NAVIGATION TEST
    - Performs login.
    - Tests the following navigation card/buttons:
      - Repositories card -> Click -> Validate -> Navigate back to dashboard explicitly.
      - Backups card -> Click -> Validate -> Navigate back to dashboard explicitly.
      - Storage card -> Click -> Validate -> Navigate back to dashboard explicitly.
      - Active Tasks (View All) -> Click -> Validate -> Navigate back to dashboard explicitly.
      - Recently Completed (View All) -> Click -> Validate -> Navigate back to dashboard explicitly.
      - Premium -> Click -> Validate -> Navigate back to dashboard explicitly.
    """
    logger.info("INFO: test step - Starting Dashboard Navigation Test")
    
    cfg = get_env_config()
    base_url = cfg["base_url"]
    workspace_id = cfg["workspace_id"]
    
    dashboard_page = perform_setup_and_login(sb)
    
    # 1. Repositories navigation
    try:
        dashboard_page.navigate_to_repositories()
        logger.info("INFO: test step - Verifying Repositories page load")
        _wait_for_url_or_content(
            sb,
            ("/repositories", "/github"),
            ("repositor", "github", "repository"),
        )
    except Exception as e:
        logger.error(f"ERROR: Repositories navigation failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)
        
    # 2. Backups navigation
    try:
        dashboard_page.navigate_to_backups()
        logger.info("INFO: test step - Verifying Backups page load")
        sb.wait_for_condition(lambda: "/backups" in sb.get_current_url(), timeout=10)
    except Exception as e:
        logger.error(f"ERROR: Backups navigation failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)
        
    # 3. Storage navigation
    try:
        dashboard_page.navigate_to_storage()
        logger.info("INFO: test step - Verifying Storage size page load")
        sb.wait_for_condition(lambda: "/storage" in sb.get_current_url(), timeout=10)
    except Exception as e:
        logger.error(f"ERROR: Storage navigation failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)
        
    # 4. Active Tasks View All navigation
    try:
        dashboard_page.navigate_to_active_tasks_view_all()
        logger.info("INFO: test step - Verifying Active Tasks View All load")
        _wait_for_url_or_content(
            sb,
            ("/activity", "/schedulers"),
            ("activity", "task", "scheduler", "execution"),
        )
    except Exception as e:
        logger.error(f"ERROR: Active Tasks View All navigation failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)
        
    # 5. Recently Completed View All navigation
    try:
        dashboard_page.navigate_to_recently_completed_view_all()
        logger.info("INFO: test step - Verifying Recently Completed View All load")
        _wait_for_url_or_content(sb, ("/activity",), ("activity", "completed", "execution"))
    except Exception as e:
        logger.error(f"ERROR: Recently Completed View All navigation failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)
        
    # 6. Premium button navigation
    try:
        dashboard_page.navigate_to_premium()
        logger.info("INFO: test step - Verifying Premium modal or page interaction")
        
        def check_premium_state():
            if "/premium" in sb.get_current_url() or "/upgrade" in sb.get_current_url():
                return True
            try:
                elements = sb.find_elements("div, h1, h2, h3, h4, button, span")
                for el in elements:
                    try:
                        txt = el.text.lower()
                        if "premium" in txt or "upgrade" in txt or "pricing" in txt:
                            if el.is_displayed():
                                return True
                    except:
                        pass
            except:
                pass
            return False
            
        sb.wait_for_condition(check_premium_state, timeout=10)
    except Exception as e:
        logger.error(f"ERROR: Premium button click failed: {str(e)}")
        raise e
    finally:
        dashboard_page.return_to_dashboard(base_url, workspace_id)

    logger.info("INFO: test step - Dashboard Navigation Test completed successfully!")
