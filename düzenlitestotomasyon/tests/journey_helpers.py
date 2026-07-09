"""Kullanici journey yardimcilari — sidebar, sayfa gezinme, cleanup."""
import logging

from tests.api_helpers import delete_backup_schedule, list_items
from utils.waits import wait_for_page_ready, wait_for_url_fragment

logger = logging.getLogger("GitsecE2E")

# Bitbucket/GitLab OAuth E2E simdilik hesap yok — sadece sayfa/API smoke test_21'de
DEFERRED_OAUTH_PROVIDERS = frozenset({"bitbucket", "gitlab"})

SIDEBAR_PAGES = (
    ("repositories", ("/repositories", "/github")),
    ("backups", ("/backups",)),
    ("storage", ("/storage",)),
    ("schedulers", ("/schedulers",)),
    ("activity", ("/activity",)),
    ("settings", ("/settings",)),
)


def workspace_url(cfg, path_suffix):
    return f"{cfg['base_url']}/{cfg['workspace_id']}/{path_suffix.lstrip('/')}"


def open_workspace_path(sb, cfg, path_suffix, *, dismiss=True):
    """Workspace altinda bir path acar ve main bekler."""
    from tests.helpers import dismiss_ui_blockers

    url = workspace_url(cfg, path_suffix)
    sb.open(url)
    wait_for_page_ready(sb)
    if dismiss:
        dismiss_ui_blockers(sb)
    return url


def assert_not_404(sb):
    body = sb.get_text("body").lower()
    assert "404" not in body and "not found" not in body, f"404 on {sb.get_current_url()}"


def visit_sidebar_or_direct(sb, cfg, page_key, url_fragments, *, already_logged_in=False):
    """Sidebar linki veya dogrudan URL ile sayfayi acar."""
    from tests.helpers import dismiss_ui_blockers, perform_setup_and_login

    if not already_logged_in:
        perform_setup_and_login(sb)
        sb.open(workspace_url(cfg, "dashboard"))
        wait_for_page_ready(sb)
        dismiss_ui_blockers(sb)

    visited = False
    nav_links = sb.find_elements("nav a[href], aside a[href]")
    for link in nav_links:
        try:
            href = link.get_attribute("href") or ""
            if cfg["workspace_id"] not in href:
                continue
            if any(frag in href for frag in url_fragments):
                sb.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                link.click()
                wait_for_page_ready(sb)
                dismiss_ui_blockers(sb)
                if any(frag in sb.get_current_url() for frag in url_fragments):
                    visited = True
                    break
        except Exception:
            continue

    if not visited:
        open_workspace_path(sb, cfg, url_fragments[0].lstrip("/"))
        wait_for_url_fragment(sb, url_fragments[0], timeout=15)

    assert_not_404(sb)
    assert sb.is_element_visible("main") or sb.is_element_present("main"), f"{page_key} main missing"
    logger.info("INFO: test step - Visited %s via %s", page_key, sb.get_current_url())
    return sb.get_current_url()


def visit_all_core_sidebar_pages(sb, cfg):
    """Tum cekirdek sidebar sayfalarini gezer."""
    from tests.helpers import dismiss_ui_blockers, perform_setup_and_login

    perform_setup_and_login(sb)
    sb.open(workspace_url(cfg, "dashboard"))
    wait_for_page_ready(sb)
    dismiss_ui_blockers(sb)

    results = {}
    for page_key, fragments in SIDEBAR_PAGES:
        try:
            url = visit_sidebar_or_direct(
                sb, cfg, page_key, fragments, already_logged_in=True
            )
            results[page_key] = url
        except Exception as exc:
            logger.warning("WARNING: Could not visit %s: %s", page_key, exc)
            results[page_key] = None
    loaded = [k for k, v in results.items() if v]
    assert len(loaded) >= 4, f"Expected >=4 sidebar pages, got {loaded}: {results}"
    return results


def delete_schedule_by_name(api_client, schedule_name):
    """Isimle schedule bulup siler."""
    status, payload = api_client.get("/api/backup/schedules/tenant")
    if status != 200:
        return False
    for item in list_items(payload):
        if not isinstance(item, dict):
            continue
        name = item.get("name") or ""
        if name == schedule_name or schedule_name in name:
            schedule_id = item.get("id") or item.get("scheduleId")
            if schedule_id:
                del_status, _ = delete_backup_schedule(api_client, schedule_id)
                return del_status in (200, 204, 404)
    return False


def page_has_table_or_content(sb, *keywords):
    body = sb.get_text("body").lower()
    if sb.is_element_present("table"):
        return True
    return any(k in body for k in keywords)
