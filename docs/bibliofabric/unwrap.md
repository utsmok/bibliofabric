# Response unwrapping

`ResponseUnwrapper` is the protocol that makes bibliofabric API-agnostic. A
client implements it to teach the framework how to navigate its API's JSON
envelope: where result records live, how to read a single item, the total, the
next cursor, and the remaining metadata.

```python
class FooUnwrapper:
    def results(self, body):
        return body.get("results", [])

    def item(self, body):
        return body

    def total(self, body):
        return body.get("total")

    def next_cursor(self, body):
        return body.get("next_cursor")

    def meta(self, body):
        return {k: v for k, v in body.items() if k != "results"}
```

No inheritance is required; any object with these five methods satisfies the
protocol.

## JSON:API unwrapping

`JsonApiUnwrapper` in `bibliofabric.unwrap` is a ready-made `ResponseUnwrapper`
for JSON:API envelopes, as served by DataCite:

```python
from bibliofabric import JsonApiUnwrapper

unwrapper = JsonApiUnwrapper(cursor_param="page[cursor]")
```

- `results()` returns the `data` list members that are objects: raw JSON:API
  resource objects with `id`, `type`, `attributes`, and `relationships`.
- `item()` returns the single `data` object, or `{}` when there is none.
- `total()` returns `meta.total` when it is an integer.
- `next_cursor()` reads the `cursor_param` query parameter from the
  `links.next` URL.
- `meta()` returns the envelope minus `data`.

## API reference

::: bibliofabric.unwrap
    options:
      show_root_heading: true
