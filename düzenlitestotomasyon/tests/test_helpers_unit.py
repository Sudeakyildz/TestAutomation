"""Unit tests for tests.helpers — staging'e gitmez."""
import os
from unittest.mock import MagicMock

import pytest

from tests.helpers import _session_needs_refresh, get_env_config, is_ci, open_add_provider_page


def test_is_ci_true_when_github_actions(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert is_ci() is True


def test_is_ci_false_by_default(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert is_ci() is False


def test_get_env_config_defaults(monkeypatch):
    monkeypatch.delenv("WORKSPACE_ID", raising=False)
    monkeypatch.delenv("GITHUB_TEST_ORG", raising=False)
    cfg = get_env_config()
    assert cfg["workspace_id"] == "83"
    assert cfg["github_test_org"] == "1testhesap234-beep"
    assert "staging.dashboard.gitsec.io" in cfg["base_url"]


def test_session_needs_refresh_on_sign_in_url():
    sb = MagicMock()
    sb.get_current_url.return_value = "https://staging.dashboard.gitsec.io/sign-in"
    assert _session_needs_refresh(sb, "https://staging.dashboard.gitsec.io", "83") is True


def test_session_needs_refresh_when_main_missing():
    sb = MagicMock()
    sb.get_current_url.return_value = "https://staging.dashboard.gitsec.io/83/dashboard"
    sb.get_text.return_value = "dashboard"
    sb.is_element_visible.side_effect = lambda sel: False
    assert _session_needs_refresh(sb, "https://staging.dashboard.gitsec.io", "83") is True


def test_open_add_provider_page_first_matching_route(monkeypatch):
    sb = MagicMock()
    sb.get_current_url.return_value = "https://staging.dashboard.gitsec.io/83/repositories/add"
    sb.get_text.return_value = "github bitbucket provider"
    sb.is_element_visible.side_effect = lambda sel: sel == "main"

    monkeypatch.setattr("tests.helpers.perform_setup_and_login", lambda _sb: None)
    monkeypatch.setattr("tests.helpers.dismiss_ui_blockers", lambda _sb: None)

    url = open_add_provider_page(sb)
    assert url.endswith("/83/repositories/add")
