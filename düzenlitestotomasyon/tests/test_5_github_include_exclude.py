import os
import sys
import time
import logging
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import (
    perform_setup_and_login,
    scroll_table_right,
    check_license_limit_or_error,
    dismiss_ui_blockers,
    toggle_repository_switch,
    get_switch_state,
    safe_click,
    click_exclude_confirm_if_any,
    get_env_config,
)
from utils.waits import wait_for_page_ready
from utils.gitsec_bug import fail_gitsec_bug

logger = logging.getLogger("GitsecE2E")


def _first_switch(sb):
    switch_sel = "table tbody tr:nth-child(1) button[role='switch']"
    return switch_sel if sb.is_element_present(switch_sel) else None


def _select_first_row(sb):
    checkbox_sel = "table tbody tr:nth-child(1) button[role='checkbox'], table tbody tr:nth-child(1) input[type='checkbox']"
    if sb.is_element_present(checkbox_sel):
        safe_click(sb, checkbox_sel, timeout=5, dismiss=False)
        time.sleep(0.5)


def _bulk_action(sb, *labels):
    for label in labels:
        btn = f"xpath=//button[contains(., '{label}')]"
        if sb.is_element_visible(btn):
            safe_click(sb, btn, timeout=5, dismiss=False)
            return True
    return False


def _refresh_and_get_state(sb, page_url, switch_sel):
    sb.open(page_url)
    time.sleep(3)
    scroll_table_right(sb)
    return get_switch_state(sb, switch_sel)


def _try_exclude(sb, switch_sel, page_url):
    """Switch + bulk exclude dener. (başarılı_mı, onay_tıklandı_mı, bulk_denendi_mi)"""
    confirm_clicked = False
    bulk_tried = False

    _select_first_row(sb)
    if _bulk_action(sb, "Exclude selected", "Exclude Selected", "Hariç tut"):
        bulk_tried = True
        confirm_clicked = click_exclude_confirm_if_any(sb)

    if _refresh_and_get_state(sb, page_url, switch_sel) is False:
        return True, confirm_clicked, bulk_tried

    if toggle_repository_switch(sb, switch_sel, False, page_url):
        return True, confirm_clicked or True, bulk_tried

    return False, confirm_clicked, bulk_tried


@pytest.mark.known_gitsec_bug
@pytest.mark.xfail(
    strict=False,
    reason="Bilinen GitSec staging bug — include/exclude persist etmiyor",
)
def test_github_repositories_include_all_then_exclude_all(sb):
    """
    GitSec staging'de repository include/exclude akışını doğrular.
    Beklenen davranış oluşmazsa olası GitSec ürün hatası olarak raporlanır.
    """
    logger.info("INFO: test step - Starting Include / Exclude Test")

    base_url = os.getenv("DASHBOARD_BASE_URL", "https://staging.dashboard.gitsec.io")
    workspace_id = os.getenv("WORKSPACE_ID", "83")
    github_repos_url = f"{base_url}/{workspace_id}/repositories/github"

    perform_setup_and_login(sb)
    sb.open(github_repos_url)
    wait_for_page_ready(sb)
    dismiss_ui_blockers(sb)
    sb.assert_element("table", timeout=30)
    scroll_table_right(sb)

    switch_sel = _first_switch(sb)
    if not switch_sel:
        pytest.skip("No repository switch found on GitHub repositories page.")

    initial_state = get_switch_state(sb, switch_sel)
    logger.info(f"INFO: test step - Row 1 initial switch state: {initial_state}")

    if initial_state is True:
        logger.info("INFO: test step - Step 1: Excluding active repository")
        ok, confirm_clicked, bulk_tried = _try_exclude(sb, switch_sel, github_repos_url)
        if not ok:
            if check_license_limit_or_error(sb):
                pytest.skip("License limit prevented exclude — ortam kısıtı.")
            fail_gitsec_bug(
                title="Repository exclude akışı persist etmiyor",
                details="Switch/bulk exclude denendi; yenileme sonrası repo hâlâ included.",
                area="Repositories / License Inclusion",
                evidence=[
                    f"Onay modalı tıklandı: {confirm_clicked}",
                    f"Bulk exclude denendi: {bulk_tried}",
                    f"URL: {sb.get_current_url()}",
                ],
            )

    logger.info("INFO: test step - Step 2: Including repository")
    if not toggle_repository_switch(sb, switch_sel, True, github_repos_url):
        if check_license_limit_or_error(sb):
            pytest.skip("License limit reached.")
        fail_gitsec_bug(
            title="Repository include akışı tamamlanmıyor",
            details="Exclude sonrası include switch'i aktif duruma geçmiyor.",
            area="Repositories / License Inclusion",
        )

    logger.info("INFO: test step - Step 3: Final exclude")
    ok, _, _ = _try_exclude(sb, switch_sel, github_repos_url)
    if not ok:
        fail_gitsec_bug(
            title="Include sonrası exclude tekrar çalışmıyor",
            details="Include → exclude döngüsünün son adımında durum kalıcı olarak excluded olmuyor.",
            area="Repositories / License Inclusion",
            evidence=[f"Final refresh state: {_refresh_and_get_state(sb, github_repos_url, switch_sel)}"],
        )

    logger.info("INFO: test step - Include / Exclude Test completed successfully!")
