# `bibliofabric`: shared core for scholarly API clients
*Samuel Mok // s.mok@utwente.nl*

`bibliofabric` is an asynchronous Python framework for building client libraries
for scholarly APIs (OpenAIRE, OpenAlex, Crossref, and similar services). It owns
what every such client needs: HTTP with retries and throttling, authentication,
error mapping, paging, batch retrieval, identifier normalization, and typed
resource clients. A client library only adds what is specific to its API.

## Installation

```bash
uv add bibliofabric
```

Requires Python 3.12 or newer.

## Building a client

A client library defines four things: a settings subclass, a response
unwrapper, a query dialect, and one `ResourceClient` subclass per endpoint.

```python
from bibliofabric import (
    BaseApiClient,
    BaseApiSettings,
    QueryDialect,
    ResourceClient,
    ResponseUnwrapper,
)
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class FooSettings(BaseApiSettings):
    model_config = SettingsConfigDict(
        env_prefix="FOO_", env_file=".env", extra="ignore"
    )


class Work(BaseModel):
    id: str = ""
    title: str = ""
    doi: str | None = None


class FooUnwrapper:
    """Unwraps the Foo API envelope: {"results": [...], "total": n}."""

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


DIALECT = QueryDialect(
    page_size_param="per_page",
    max_page_size=200,
    query_param="search",
    select_param="select",
)


class Works(ResourceClient[Work]):
    path = "works"
    model = Work
    dialect = DIALECT


class FooClient(BaseApiClient):
    def __init__(self, settings=None, auth=None):
        super().__init__(
            base_url="https://api.foo.org/v1",
            settings=settings or FooSettings(),
            unwrapper=FooUnwrapper(),
            auth=auth,
        )
        self.works = Works(self)
```

Using the client:

```python
async with FooClient() as client:
    work = await client.works.get("W123")  # 404 raises NotFoundError
    page = await client.works.search(query="algae")  # returns Page[Work]
    async for work in client.works.iterate(page_size=100, limit=500):
        ...
    count = await client.works.count()
    batch = await client.works.batch_get(["W1", "W2", "W3"])
```

`get()`, `search()`, and `count()` return typed results; iteration supports
cursor, page, and offset paging depending on the dialect. Errors, retries, and
limits are described in the [errors page](https://utsmok.github.io/bibliofabric/bibliofabric/errors/).

Every client built on the framework also gets a generated sync twin. Sync
classes follow the `FooClient` -> `FooSyncClient` naming rule:

```python
with FooSyncClient() as client:
    work = client.works.get("W123")
    page = client.works.search(query="algae")
    for work in client.works.iterate(page_size=100, limit=500):
        ...
```

The sync client uses `httpx.Client`, `time.sleep`, and threads; it never
starts an event loop, so it works in plain scripts, in Jupyter, and inside a
running event loop. See the "Sync usage" docs page.

## Reference clients

- [AIREloom](https://github.com/utsmok/bibliofabric/tree/main/packages/aireloom) — OpenAIRE Graph and Scholix
- [aletheca](https://github.com/utsmok/bibliofabric/tree/main/packages/aletheca) — OpenAlex
- [stavrophora](https://github.com/utsmok/bibliofabric/tree/main/packages/stavrophora) — Crossref

## Contributing and license

See the [contributing guide](https://utsmok.github.io/bibliofabric/contributing/).
This project is licensed under the MIT License.
