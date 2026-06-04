# Models & Protocols

The `ResponseUnwrapper` protocol is the key abstraction that makes bibliofabric API-agnostic. Instead of hardcoding response parsing, `BaseApiClient` delegates to an unwrapper that knows how to extract results, pagination tokens, and totals from a specific API's JSON envelope.

Implement the protocol for your API by defining how to navigate its response structure:

```python
from bibliofabric.models import ResponseUnwrapper

class MyApiUnwrapper(ResponseUnwrapper):
    def unwrap_results(self, response_json: dict) -> list[dict]:
        return response_json.get("items", [])

    def unwrap_single_item(self, response_json: dict) -> dict:
        return response_json.get("item", {})

    def get_next_page_token(self, response_json: dict) -> str | None:
        return response_json.get("next_cursor")

    def get_total_results(self, response_json: dict) -> int | None:
        return response_json.get("total_count")
```

## API Reference

::: bibliofabric.models
    options:
      show_source: false
      show_root_heading: true
