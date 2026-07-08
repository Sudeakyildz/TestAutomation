"""Unit tests for api_helpers — saf Python, staging'e gitmez."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.api_helpers import (
    build_backup_schedule_body,
    extract_id,
    first_list_item,
    list_items,
    unique_name,
)


def test_extract_id_from_nested_data():
    payload = {"success": True, "data": {"scheduleId": 418, "id": 0}}
    assert extract_id(payload, "id", "scheduleId") == 418


def test_extract_id_skips_zero():
    payload = {"data": {"id": 0, "userInviteId": 44}}
    assert extract_id(payload, "id", "userInviteId") == 44


def test_first_list_item_dict_list():
    payload = {"data": {"list": [{"id": 1}, {"id": 2}]}}
    assert first_list_item(payload)["id"] == 1


def test_list_items_from_data_list():
    payload = {"data": [{"id": 1}, {"id": 2}]}
    assert len(list_items(payload)) == 2


def test_build_backup_schedule_body():
    body = build_backup_schedule_body("test-sched", 1154, 83)
    assert body["repositoryId"] == 1154
    assert body["workspaceId"] == 83
    assert body["triggerType"] == "Cron"
    assert "cronExpression" in body


def test_unique_name_prefix():
    name = unique_name("unit")
    assert name.startswith("unit-")
