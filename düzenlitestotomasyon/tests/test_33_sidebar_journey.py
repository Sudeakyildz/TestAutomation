"""
33. SIDEBAR JOURNEY
Tum cekirdek sidebar sayfalarina gezinme — kullanici ana navigasyon akisi.
"""
import logging

from tests.helpers import get_env_config
from tests.journey_helpers import visit_all_core_sidebar_pages

logger = logging.getLogger("GitsecE2E")


def test_sidebar_core_pages_journey(sb):
    """Sidebar veya direct URL ile repositories, backups, storage, schedulers, activity, settings."""
    cfg = get_env_config()
    results = visit_all_core_sidebar_pages(sb, cfg)
    logger.info("INFO: test step - Sidebar journey completed: %s", list(results.keys()))


def test_schedulers_sidebar_direct(sb):
    """Schedulers sayfasi dogrudan acilir."""
    from tests.journey_helpers import open_workspace_path, assert_not_404
    from tests.helpers import perform_setup_and_login, assert_main_visible

    cfg = get_env_config()
    perform_setup_and_login(sb)
    open_workspace_path(sb, cfg, "schedulers")
    assert_not_404(sb)
    assert_main_visible(sb)
    assert "/schedulers" in sb.get_current_url()
