"""API response sozlesme dogrulama — exploratory testlerde gevsek, smoke'ta siki."""
from typing import Any


def assert_json_object(payload: Any, endpoint: str = "") -> dict:
    assert isinstance(payload, dict), f"{endpoint}: expected JSON object, got {type(payload)}"
    return payload


def assert_success_envelope(status: int, payload: Any, endpoint: str = "") -> dict:
    """200 + success=true + data object/list."""
    assert status == 200, f"{endpoint}: expected HTTP 200, got {status}"
    body = assert_json_object(payload, endpoint)
    assert body.get("success") is True, f"{endpoint}: success=false — {body}"
    assert "data" in body, f"{endpoint}: missing data field — {body}"
    return body


def assert_data_has_list(payload: Any, endpoint: str = "", list_key: str = "list") -> list:
    """200 success yanitinda liste alanini dogrular."""
    if isinstance(payload, dict) and payload.get("success") is True:
        data = payload.get("data")
    else:
        data = payload
    if isinstance(data, dict):
        items = data.get(list_key)
        if items is None and list_key == "list":
            items = data.get("items")
        assert isinstance(items, list), f"{endpoint}: expected list under data.{list_key}"
        return items
    if isinstance(data, list):
        return data
    raise AssertionError(f"{endpoint}: expected list in response data")


def assert_optional_success(status: int, payload: Any, endpoint: str = ""):
    """200 ise success envelope dogrula; diger statuslerde sadece tip kontrolu."""
    if status != 200:
        return
    if isinstance(payload, dict) and "success" in payload:
        assert payload.get("success") is True, f"{endpoint}: success=false — {payload}"
