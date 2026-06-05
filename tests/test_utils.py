# tests/test_utils.py
from pydantic import BaseModel

from bibliofabric.utils import DigMixin, safe_dig


class Inner(BaseModel):
    name: str = ""
    value: int | None = None


class Outer(BaseModel):
    inner: Inner | None = None
    label: str | None = None


class TestSafeDig:
    def test_basic_attr(self):
        obj = Inner(name="test", value=42)
        assert safe_dig(obj, "name") == "test"
        assert safe_dig(obj, "value") == 42

    def test_missing_attr(self):
        obj = Inner(name="test")
        assert safe_dig(obj, "nonexistent") is None
        assert safe_dig(obj, "nonexistent", default="fallback") == "fallback"

    def test_nested_attr(self):
        obj = Outer(inner=Inner(name="deep"))
        assert safe_dig(obj, "inner", "name") == "deep"

    def test_none_in_chain(self):
        obj = Outer(inner=None)
        assert safe_dig(obj, "inner", "name") is None
        assert safe_dig(obj, "inner", "name", default="missing") == "missing"

    def test_dict_access(self):
        data = {"a": {"b": 42}}
        assert safe_dig(data, "a", "b") == 42

    def test_dict_missing_key(self):
        data = {"a": {}}
        assert safe_dig(data, "a", "c") is None

    def test_none_root(self):
        assert safe_dig(None, "anything") is None


class TestDigMixin:
    def test_dig_on_model(self):
        class MyModel(BaseModel, DigMixin):
            inner: Inner | None = None

        m = MyModel(inner=Inner(name="hello"))
        assert m.dig("inner", "name") == "hello"

    def test_dig_missing(self):
        class MyModel(BaseModel, DigMixin):
            inner: Inner | None = None

        m = MyModel(inner=None)
        assert m.dig("inner", "name") is None
        assert m.dig("inner", "name", default="N/A") == "N/A"
