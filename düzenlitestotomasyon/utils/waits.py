"""Explicit wait yardimcilari — time.sleep yerine kosul bazli bekleme."""
import time


def wait_for_workspace_dashboard(sb, workspace_id, timeout=25):
    """Workspace dashboard URL ve main iceriginin yuklenmesini bekler."""
    fragment = f"/{workspace_id}/"
    sb.wait_for_condition(lambda: fragment in sb.get_current_url(), timeout=timeout)
    sb.assert_element("main", timeout=timeout)


def wait_for_page_ready(sb, timeout=20):
    """Sayfa DOM'unun hazir olmasini bekler (main veya body)."""
    try:
        sb.wait_for_condition(
            lambda: sb.is_element_visible("main") or sb.is_element_visible("body"),
            timeout=timeout,
        )
    except Exception:
        sb.assert_element("body", timeout=5)


def wait_for_url_fragment(sb, fragment, timeout=20):
    sb.wait_for_condition(lambda: fragment in sb.get_current_url(), timeout=timeout)


def wait_for_body_text(sb, *keywords, timeout=30):
    """Body metninde anahtar kelimelerden biri gorunene kadar bekler."""
    lowered = [k.lower() for k in keywords]

    def _found():
        try:
            body = sb.get_text("body").lower()
        except Exception:
            return False
        return any(k in body for k in lowered)

    sb.wait_for_condition(_found, timeout=timeout)


def wait_for_element_stable(sb, selector, timeout=15, poll=0.25):
    """Element gorunur olana kadar bekler."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if sb.is_element_visible(selector):
                return True
        except Exception:
            pass
        time.sleep(poll)
    sb.wait_for_element_visible(selector, timeout=2)
    return True


def wait_for_dialog_closed(sb, selector="div[role='dialog']", timeout=10):
    """Modal/dialog kapanana kadar bekler."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if not sb.is_element_visible(selector):
                return True
        except Exception:
            return True
        time.sleep(0.25)
    return False
