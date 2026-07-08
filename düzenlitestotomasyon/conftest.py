import os
import logging
import pytest
from dotenv import load_dotenv

SMOKE_MODULES = {
    "test_0_api_staging.py",
    "test_1_login.py",
    "test_2_dashboard_navigation.py",
}

EXPLORATORY_MODULES = {
    "test_20_api_comprehensive.py",
}

WRITE_MODULES = {
    "test_29_sandbox_writes.py",
}

FUNCTIONAL_API_MODULES = {
    "test_22_workspace_team_actions.py",
    "test_24_backup_functional.py",
    "test_25_restore_functional.py",
    "test_26_scheduler_crud.py",
    "test_27_storage_functional.py",
    "test_29_sandbox_writes.py",
}

UNIT_MODULES = {
    "test_api_helpers_unit.py",
}

KNOWN_GITSEC_BUG_MODULES = {
    "test_5_github_include_exclude.py",
    "test_7_backups_restore.py",
}

GITHUB_MODULES = {
    "test_4_github_repositories.py",
    "test_5_github_include_exclude.py",
    "test_6_github_backup_combinations.py",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("GitsecE2E")

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
root_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(root_env_path):
    load_dotenv(dotenv_path=root_env_path)


def pytest_addoption(parser):
    parser.addoption(
        "--skip-preflight",
        action="store_true",
        default=False,
        help="Staging preflight kontrollerini atla",
    )


def pytest_configure(config):
    if os.getenv("GITSEC_HTML_REPORT") == "1":
        config.option.htmlpath = os.path.join(
            os.path.dirname(__file__), "reports", "report.html"
        )
        config.option.self_contained_html = True


def pytest_collection_finish(session):
    if session.config.getoption("--skip-preflight") or os.getenv("GITSEC_SKIP_PREFLIGHT") == "1":
        return

    staging_items = [
        item
        for item in session.items
        if os.path.basename(str(item.fspath)) not in UNIT_MODULES
    ]
    if not staging_items:
        return

    from tests.preflight import run_preflight

    errors = run_preflight()
    if errors:
        msg = "Staging preflight failed:\n" + "\n".join(f"  - {e}" for e in errors)
        pytest.exit(msg, returncode=1)


@pytest.fixture(scope="module")
def api_client():
    from utils.api_client import GitsecApiClient

    email = os.getenv("E2E_USER_EMAIL")
    password = os.getenv("E2E_USER_PASSWORD")
    assert email, "E2E_USER_EMAIL environment variable is not defined"
    assert password, "E2E_USER_PASSWORD environment variable is not defined"

    client = GitsecApiClient()
    client.sign_in(email, password)
    return client


@pytest.fixture(scope="module")
def workspace_id():
    ws = os.getenv("WORKSPACE_ID")
    assert ws, "WORKSPACE_ID environment variable is not defined"
    return ws


@pytest.fixture(scope="module")
def tenant_repository_id(api_client):
    from tests.api_helpers import get_first_repository

    repo_id, status, _ = get_first_repository(api_client)
    if not repo_id:
        pytest.skip(f"Tenant repository yok (HTTP {status})")
    return repo_id


@pytest.fixture(scope="module")
def tenant_backup_schedule_id(api_client):
    from tests.api_helpers import get_first_backup_schedule

    schedule_id, _, _ = get_first_backup_schedule(api_client)
    if not schedule_id:
        pytest.skip("Tenant backup schedule yok")
    return schedule_id


@pytest.fixture(autouse=True)
def patch_sb_fixture(request):
    if "sb" not in request.fixturenames:
        return

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
        assert substring in sb.get_current_url(), (
            f"URL did not contain '{substring}' within {limit} seconds. "
            f"Current URL: {sb.get_current_url()}"
        )

    sb.wait_for_condition = wait_for_condition
    sb.assert_url_contains = assert_url_contains

    methods_to_wrap = [
        "click", "type", "wait_for_element_visible", "is_element_visible",
        "wait_for_element_present", "is_element_present", "scroll_to",
        "get_text", "assert_text", "assert_element", "wait_for_element",
        "remove_element", "find_element", "find_elements",
    ]

    for name in methods_to_wrap:
        if hasattr(sb, name):
            orig = getattr(sb, name)

            def make_wrapper(original_method):
                def wrapper(selector, *args, **kwargs):
                    if (
                        isinstance(selector, str)
                        and (selector.startswith("/") or selector.startswith("("))
                        and not selector.startswith("xpath=")
                    ):
                        selector = f"xpath={selector}"
                    return original_method(selector, *args, **kwargs)

                return wrapper

            setattr(sb, name, make_wrapper(orig))


def pytest_collection_modifyitems(config, items):
    for item in items:
        module_name = os.path.basename(str(item.fspath))

        if module_name in UNIT_MODULES:
            item.add_marker(pytest.mark.unit)
            continue

        if module_name in SMOKE_MODULES:
            item.add_marker(pytest.mark.smoke)
        elif module_name not in EXPLORATORY_MODULES:
            item.add_marker(pytest.mark.regression)

        if module_name in EXPLORATORY_MODULES:
            item.add_marker(pytest.mark.exploratory)

        if module_name in WRITE_MODULES:
            item.add_marker(pytest.mark.write)

        if module_name in FUNCTIONAL_API_MODULES:
            item.add_marker(pytest.mark.functional)

        if module_name in KNOWN_GITSEC_BUG_MODULES:
            item.add_marker(pytest.mark.known_gitsec_bug)
            item.add_marker(
                pytest.mark.xfail(
                    strict=False,
                    reason="Bilinen GitSec staging bug — overlay/modal veya license akışı",
                )
            )

        if module_name in GITHUB_MODULES:
            item.add_marker(pytest.mark.requires_github)

        uses_sb = "sb" in item.fixturenames
        uses_api = "api_client" in item.fixturenames

        if uses_sb:
            item.add_marker(pytest.mark.e2e)
        if uses_api and not uses_sb:
            item.add_marker(pytest.mark.api)
        elif module_name in SMOKE_MODULES | EXPLORATORY_MODULES | WRITE_MODULES | FUNCTIONAL_API_MODULES:
            item.add_marker(pytest.mark.api)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.skipped:
        logger.warning("SKIPPED: %s — %s", item.nodeid, report.longrepr)
