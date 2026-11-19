"""Tests for bibliofabric.safe_types — SafeList and SafeStr."""

from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from bibliofabric.safe_types import SafeList, SafeStr


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class Container(BaseModel):
    items: SafeList[str] = Field(default_factory=list)
    name: SafeStr = ""


class Nested(BaseModel):
    value: SafeStr = ""


class WithNestedList(BaseModel):
    children: SafeList[Nested] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# SafeStr tests
# ---------------------------------------------------------------------------


class TestSafeStr:
    def test_none_coerced_to_empty(self) -> None:
        m = Container.model_validate({"items": [], "name": None})
        assert m.name == ""

    def test_non_none_passthrough(self) -> None:
        m = Container.model_validate({"name": "hello"})
        assert m.name == "hello"

    def test_empty_string_passthrough(self) -> None:
        m = Container.model_validate({"name": ""})
        assert m.name == ""

    def test_default_when_key_missing(self) -> None:
        m = Container.model_validate({})
        assert m.name == ""

    def test_string_methods_work_without_guards(self) -> None:
        m = Container.model_validate({"name": None})
        assert m.name.upper() == ""


# ---------------------------------------------------------------------------
# SafeList tests
# ---------------------------------------------------------------------------


class TestSafeList:
    def test_none_coerced_to_empty_list(self) -> None:
        m = Container.model_validate({"items": None})
        assert m.items == []

    def test_null_elements_stripped(self) -> None:
        m = Container.model_validate({"items": ["a", None, "b", None, "c"]})
        assert m.items == ["a", "b", "c"]

    def test_all_null_elements_yield_empty(self) -> None:
        m = Container.model_validate({"items": [None, None]})
        assert m.items == []

    def test_non_none_passthrough(self) -> None:
        m = Container.model_validate({"items": ["x", "y"]})
        assert m.items == ["x", "y"]

    def test_default_factory_when_key_missing(self) -> None:
        m = Container.model_validate({})
        assert m.items == []

    def test_empty_list_passthrough(self) -> None:
        m = Container.model_validate({"items": []})
        assert m.items == []

    def test_nested_model_list_with_nulls(self) -> None:
        m = WithNestedList.model_validate(
            {"children": [None, {"value": "a"}, None, {"value": "b"}]}
        )
        assert len(m.children) == 2
        assert m.children[0].value == "a"
        assert m.children[1].value == "b"

    def test_nested_model_list_none_coerced(self) -> None:
        m = WithNestedList.model_validate({"children": None})
        assert m.children == []

    def test_iterable_without_guards(self) -> None:
        """SafeList fields should be safely iterable even when API returns null."""
        m = Container.model_validate({"items": None})
        result = [x.upper() for x in m.items]
        assert result == []


# ---------------------------------------------------------------------------
# Combined behavior
# ---------------------------------------------------------------------------


class TestCombined:
    def test_both_fields_none(self) -> None:
        m = Container.model_validate({"items": None, "name": None})
        assert m.items == []
        assert m.name == ""

    def test_both_fields_present(self) -> None:
        m = Container.model_validate({"items": ["a"], "name": "test"})
        assert m.items == ["a"]
        assert m.name == "test"

    def test_model_dump_round_trip(self) -> None:
        data = {"items": ["a", None, "b"], "name": None}
        m = Container.model_validate(data)
        dumped = m.model_dump()
        assert dumped == {"items": ["a", "b"], "name": ""}
        # Validate again from dumped data
        m2 = Container.model_validate(dumped)
        assert m2.items == ["a", "b"]
        assert m2.name == ""
