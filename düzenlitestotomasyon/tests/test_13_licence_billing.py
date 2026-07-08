"""
13. LİSANS & BİLLİNG TEST
Premium sayfası, plan bilgileri ve kullanım özeti.
"""
import os
import sys
import time
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.helpers import perform_setup_and_login, dismiss_ui_blockers, get_env_config, assert_main_visible
from utils.api_client import GitsecApiClient

logger = logging.getLogger("GitsecE2E")


def test_premium_page_from_dashboard(sb):
    """Dashboard premium/upgrade butonu billing/premium içeriği açar."""
    from pages.dashboard_page import DashboardPage

    cfg = get_env_config()
    dashboard = perform_setup_and_login(sb)
    dashboard.navigate_to_premium()
    body = sb.get_text("body").lower()
    assert any(k in body for k in ["premium", "upgrade", "plan", "pricing", "freemium"])
    dashboard.return_to_dashboard(cfg["base_url"], cfg["workspace_id"])
    logger.info("INFO: test step - Premium/billing content visible")


def test_billing_page_direct(sb):
    """Billing sayfasına doğrudan navigasyon."""
    cfg = get_env_config()
    perform_setup_and_login(sb)
    for path in ["billing", "premium", "upgrade"]:
        sb.open(f"{cfg['base_url']}/{cfg['workspace_id']}/{path}")
        time.sleep(3)
        dismiss_ui_blockers(sb)
        if sb.is_element_visible("main") and "404" not in sb.get_text("body").lower():
            logger.info(f"INFO: test step - Billing page loaded at /{path}")
            return
    logger.info("INFO: test step - Billing via modal only — API ile doğrulanıyor")


def test_billing_page_direct_api_fallback(api_client):
    """Billing route yoksa licence API ile doğrula."""
    status, payload = api_client.get("/api/licences/current")
    GitsecApiClient.assert_success(status, payload, "/api/licences/current")
    assert payload["data"]["status"]


def test_current_licence_api(api_client):
    """Mevcut lisans bilgisi."""
    status, payload = api_client.get("/api/licences/current")
    GitsecApiClient.assert_success(status, payload, "/api/licences/current")
    assert payload["data"]["status"]
    logger.info("INFO: test step - Current licence API OK")


def test_usage_summary_api(api_client):
    """Lisans kullanım özeti."""
    status, payload = api_client.get("/api/licences/usage-summary")
    GitsecApiClient.assert_success(status, payload, "/api/licences/usage-summary")
    logger.info("INFO: test step - Usage summary API OK")


def test_licence_plans_api(api_client):
    """Plan listesi."""
    status, payload = api_client.get("/api/licence-mapping/plans")
    GitsecApiClient.assert_success(status, payload, "/api/licence-mapping/plans")
    logger.info("INFO: test step - Licence plans API OK")


def test_remaining_limits_api(api_client):
    """Kalan limitler."""
    status, payload = api_client.get("/api/licences/remaining-limits")
    assert status in (200, 404, 422), f"Unexpected status: {status}"
    logger.info("INFO: test step - Remaining limits API responded")


def test_upgrade_preview_api(api_client):
    """Upgrade preview (read-only)."""
    status, payload = api_client.get("/api/licences/upgrade/preview")
    assert status in (200, 400, 405, 422), f"Unexpected status: {status}"
    logger.info("INFO: test step - Upgrade preview API responded")


def test_licence_audit_history_api(api_client):
    """Lisans audit geçmişi."""
    status, payload = api_client.get("/api/licences/audit-history")
    assert status in (200, 404), f"Unexpected status: {status}"
    logger.info("INFO: test step - Licence audit history API responded")
