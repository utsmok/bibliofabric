# Types

`bibliofabric.types` provides annotated pydantic types for tolerant field
validation. Both use `BeforeValidator`, so coercion happens before core
validation and defaults still apply when the API omits the field.

```python
class Container(BaseModel):
    name: SafeStr = ""
    keywords: SafeList[str] = []
```

- `SafeStr` coerces `None` to `""`.
- `SafeList` coerces `None` to `[]`, strips null entries, and wraps a scalar
  string into a single-element list instead of a character list.

## API reference

::: bibliofabric.types
    options:
      show_root_heading: true
