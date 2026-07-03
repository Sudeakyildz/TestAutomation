import os
import logging
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GitsecE2E")

# Load environment variables from local .env and root .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
root_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(root_env_path):
    load_dotenv(dotenv_path=root_env_path)



@pytest.fixture(autouse=True)
def patch_sb_fixture(request):
    """
    Autouse fixture to intercept tests using 'sb' and patch the SeleniumBase BaseCase
    instance with 'wait_for_condition' and a wrapper for 'assert_url_contains' to support custom timeouts.
    """
    if "sb" in request.fixturenames:
        sb = request.getfixturevalue("sb")
        def wait_for_condition(condition_func, timeout=30, poll=0.5):
            import time
            start = time.time()
            while time.time() - start < timeout:
                try:
                    if condition_func():
                        return True
                except Exception:
                    pass
                time.sleep(poll)
            raise TimeoutError(f"Condition not met within {timeout} seconds.")
            
        def assert_url_contains(substring, timeout=None):
            import time
            limit = timeout if timeout is not None else 10
            start = time.time()
            while time.time() - start < limit:
                try:
                    if substring in sb.get_current_url():
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            assert substring in sb.get_current_url(), f"URL did not contain '{substring}' within {limit} seconds. Current URL: {sb.get_current_url()}"
            
        sb.wait_for_condition = wait_for_condition
        sb.assert_url_contains = assert_url_contains

        # Intercept and auto-prefix XPath selectors for CDP mode compatibility
        methods_to_wrap = [
            "click", "type", "wait_for_element_visible", "is_element_visible",
            "wait_for_element_present", "is_element_present", "scroll_to",
            "get_text", "assert_text", "assert_element", "wait_for_element",
            "remove_element", "find_element", "find_elements"
        ]
        
        for name in methods_to_wrap:
            if hasattr(sb, name):
                orig = getattr(sb, name)
                def make_wrapper(original_method):
                    def wrapper(selector, *args, **kwargs):
                        if isinstance(selector, str) and (selector.startswith("/") or selector.startswith("(")) and not selector.startswith("xpath="):
                            selector = f"xpath={selector}"
                        return original_method(selector, *args, **kwargs)
                    return wrapper
                setattr(sb, name, make_wrapper(orig))



