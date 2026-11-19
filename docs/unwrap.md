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

## API reference

::: bibliofabric.unwrap
    options:
      show_root_heading: true
