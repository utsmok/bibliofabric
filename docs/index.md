# The bibliofabric family

Four Python client libraries for scholarly metadata APIs, sharing one core:
[`bibliofabric`](bibliofabric/index.md) owns HTTP, authentication, retries,
rate limiting, paging, batch retrieval, identifier normalization, and typed
resource clients. Each library adds only what is specific to its API. All four
ship async clients alongside generated sync twins (`<Name>SyncClient`) and
`py.typed`. They live in one uv workspace at
[github.com/utsmok/bibliofabric](https://github.com/utsmok/bibliofabric)
(`packages/<name>`); this site documents all of them.

| Package | API | PyPI | Install |
|---|---|---|---|
| [bibliofabric](bibliofabric/index.md) | (core framework, no API) | [pypi.org/project/bibliofabric](https://pypi.org/project/bibliofabric/) | `uv add bibliofabric` |
| [aireloom](aireloom/index.md) | OpenAIRE Graph API (V4), Scholexplorer | [pypi.org/project/aireloom](https://pypi.org/project/aireloom/) | `uv add aireloom` |
| [aletheca](aletheca/index.md) | OpenAlex | [pypi.org/project/aletheca](https://pypi.org/project/aletheca/) | `uv add aletheca` |
| [stavrophora](stavrophora/index.md) | Crossref REST API | [pypi.org/project/stavrophora](https://pypi.org/project/stavrophora/) | `uv add stavrophora` |

## Which package do I need?

- You want records from **OpenAIRE** (research products, projects,
  organizations, persons, Scholix links): use **aireloom**.
- You want records from **OpenAlex** (works, authors, institutions,
  funders, sources): use **aletheca**.
- You want records from **Crossref** (works, journals, funders, members):
  use **stavrophora**.
- You are building a client for **another scholarly API** in this style:
  build on **bibliofabric**. Its [quick start](bibliofabric/client.md) shows
  the four pieces a client defines: a settings class, an unwrapper, a query
  dialect, and one resource client per endpoint.

Requires Python 3.12 or newer. See the [contributing guide](contributing.md)
to set up the workspace and run the test and lint gates.
