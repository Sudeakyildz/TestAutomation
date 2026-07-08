"""Unit tests for utils.api_contract."""
import pytest

from utils.api_contract import (
    assert_data_has_list,
    assert_json_object,
    assert_optional_success,
    assert_success_envelope,
)


def test_assert_success_envelope_ok():
    payload = {"success": True, "data": {"list": [1]}}
    body = assert_success_envelope(200, payload, "/api/x")
    assert body["data"]["list"] == [1]


def test_assert_success_envelope_rejects_non_200():
    with pytest.raises(AssertionError):
        assert_success_envelope(404, {"success": False}, "/api/x")


def test_assert_data_has_list_from_data_list():
    payload = {"success": True, "data": {"list": [{"id": 1}]}}
    items = assert_data_has_list(payload, "/api/x")
    assert len(items) == 1


def test_assert_optional_success_on_200():
    assert_optional_success(200, {"success": True, "data": {}})


def test_assert_json_object_rejects_string():
    with pytest.raises(AssertionError):
        assert_json_object("not-json")
