from typing import Any

import pytest

from bibliofabric.models import ResponseUnwrapper


# A dummy implementation for testing purposes
class DummyUnwrapper(ResponseUnwrapper):
    def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        return response_json.get("items", [])

    def unwrap_single_item(
        self, response_json: dict[str, Any]
    ) -> dict[str, Any] | None:
        items = response_json.get("items")
        if items and isinstance(items, list) and len(items) > 0:
            return items[0]
        return None

    def get_next_page_token(self, response_json: dict[str, Any]) -> str | None:
        return response_json.get("pagination", {}).get("next_token")

    def get_total_results(self, response_json: dict[str, Any]) -> int | None:
        return response_json.get("pagination", {}).get("total_count")


@pytest.fixture
def dummy_unwrapper() -> DummyUnwrapper:
    return DummyUnwrapper()


def test_dummy_unwrapper_unwrap_results(dummy_unwrapper: DummyUnwrapper):
    response = {"items": [{"id": 1}, {"id": 2}]}
    assert dummy_unwrapper.unwrap_results(response) == [{"id": 1}, {"id": 2}]
    assert dummy_unwrapper.unwrap_results({}) == []


def test_dummy_unwrapper_unwrap_single_item(dummy_unwrapper: DummyUnwrapper):
    response_one = {"items": [{"id": 1}]}
    assert dummy_unwrapper.unwrap_single_item(response_one) == {"id": 1}
    response_many = {"items": [{"id": 1}, {"id": 2}]}
    assert dummy_unwrapper.unwrap_single_item(response_many) == {"id": 1}
    assert dummy_unwrapper.unwrap_single_item({}) is None
    assert dummy_unwrapper.unwrap_single_item({"items": []}) is None


def test_dummy_unwrapper_get_next_page_token(dummy_unwrapper: DummyUnwrapper):
    response = {"pagination": {"next_token": "token123"}}
    assert dummy_unwrapper.get_next_page_token(response) == "token123"
    assert dummy_unwrapper.get_next_page_token({}) is None
    assert dummy_unwrapper.get_next_page_token({"pagination": {}}) is None


def test_dummy_unwrapper_get_total_results(dummy_unwrapper: DummyUnwrapper):
    response = {"pagination": {"total_count": 100}}
    assert dummy_unwrapper.get_total_results(response) == 100
    assert dummy_unwrapper.get_total_results({}) is None
    assert dummy_unwrapper.get_total_results({"pagination": {}}) is None


def test_protocol_definition_exists():
    """This test doesn't execute the protocol but checks its presence."""
    assert ResponseUnwrapper is not None
    # Further checks could involve isinstance with a valid implementer,
    # but the dummy unwrapper tests cover the methods.
    unwrapper_instance = DummyUnwrapper()
    assert isinstance(unwrapper_instance, ResponseUnwrapper)


# Example of a class that correctly implements the protocol
class ValidUnwrapperImpl(ResponseUnwrapper):
    def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        return []

    def unwrap_single_item(
        self, response_json: dict[str, Any]
    ) -> dict[str, Any] | None:
        return None

    def get_next_page_token(self, response_json: dict[str, Any]) -> str | None:
        return None

    def get_total_results(self, response_json: dict[str, Any]) -> int | None:
        return None


# Example of a class that INCORRECTLY implements (e.g. missing a method)
# This would typically be caught by a static type checker like Mypy, not easily by pytest
# class InvalidUnwrapperImpl(ResponseUnwrapper):
#     def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]: return []
# unwrap_single_item is missing


def test_valid_implementation_isinstance_check():
    valid_impl = ValidUnwrapperImpl()
    assert isinstance(valid_impl, ResponseUnwrapper)
    # If InvalidUnwrapperImpl was defined and instantiated,
    # assert isinstance(invalid_impl, ResponseUnwrapper) would also be True
    # due to structural subtyping of Protocols, as long as the methods it *does*
    # implement match the signature. Static analysis is key for protocol adherence.
    # Pytest tests typically focus on concrete implementations.
