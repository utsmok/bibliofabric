# The bibliofabric family

Python client libraries for scholarly metadata APIs, built on one core:
[`bibliofabric`](bibliofabric/index.md) owns HTTP, authentication, retries,
rate limiting, paging, batch retrieval, identifier normalization, and typed
resource clients. Each client library adds only what is specific to its API. All
ship async clients alongside generated sync twins (`<Name>SyncClient`) and
`py.typed`. They live in one uv workspace at
[github.com/utsmok/bibliofabric](https://github.com/utsmok/bibliofabric)
(`packages/<name>`); this site documents all of them. Three client libraries
are published on PyPI. Eleven more Wave 1 libraries are built in the
workspace and wait for their first release; the second table lists them.

| Package | API | PyPI | Install |
|---|---|---|---|
| [bibliofabric](bibliofabric/index.md) | (core framework, no API) | [pypi.org/project/bibliofabric](https://pypi.org/project/bibliofabric/) | `uv add bibliofabric` |
| [aireloom](aireloom/index.md) | OpenAIRE Graph API (V4), Scholexplorer | [pypi.org/project/aireloom](https://pypi.org/project/aireloom/) | `uv add aireloom` |
| [aletheca](aletheca/index.md) | OpenAlex | [pypi.org/project/aletheca](https://pypi.org/project/aletheca/) | `uv add aletheca` |
| [stavrophora](stavrophora/index.md) | Crossref REST API | [pypi.org/project/stavrophora](https://pypi.org/project/stavrophora/) | `uv add stavrophora` |

## Wave 1 libraries

These packages are complete and tested but not yet published on PyPI. Until
their first release they install from the workspace only. The
[Wave 1 roster](roadmap/wave-1-libraries.md) lists the upstream API of each
one, and the [deferred list](roadmap/deferred.md) records what each one leaves
out.

| Package | API | PyPI |
|---|---|---|
| [rorifer](rorifer/index.md) | ROR (research organizations and funders) | not published |
| [zenotheca](zenotheca/index.md) | Zenodo REST API and OAI-PMH | not published |
| [dataphora](dataphora/index.md) | DataCite REST API and public GraphQL | not published |
| [opcitato](opcitato/index.md) | OpenCitations Index and Meta APIs | not published |
| [hodoi](hodoi/index.md) | DOI registration agency lookup, content negotiation, and Handle records | not published |
| [scholiast](scholiast/index.md) | Semantic Scholar Graph, Recommendations, and Datasets APIs | not published |
| [orchis](orchis/index.md) | ORCID Public API v3.0 | not published |
| [europaea](europaea/index.md) | Europe PMC REST web services and annotations API | not published |
| [quiddita](quiddita/index.md) | Wikidata (action API, REST API, and SPARQL) | not published |
| [diurnalia](diurnalia/index.md) | DOAJ (open access journals and articles) | not published |
| [seriatim](seriatim/index.md) | ISSN Portal | not published |

## Wave 2 libraries

Wave 2 adds specialist sources. The first library is built and not yet published.

| Package | API | PyPI |
|---|---|---|
| [archeion](archeion/index.md) | arXiv API | not published |

## Which package do I need?

- You want records from **OpenAIRE** (research products, projects,
  organizations, persons, Scholix links): use **aireloom**.
- You want records from **OpenAlex** (works, authors, institutions,
  funders, sources): use **aletheca**.
- You want records from **Crossref** (works, journals, funders, members):
  use **stavrophora**.
- You want records from **ROR**: use **rorifer**.
- You want records from **Zenodo**: use **zenotheca**.
- You want records from **DataCite**: use **dataphora**.
- You want citation links from **OpenCitations**: use **opcitato**.
- You want to resolve a **DOI** (registration agency, metadata, or Handle
  record): use **hodoi**.
- You want records from **Semantic Scholar**: use **scholiast**.
- You want records from **ORCID**: use **orchis**.
- You want records from **Europe PMC**: use **europaea**.
- You want records from **Wikidata**: use **quiddita**.
- You want records from **DOAJ**: use **diurnalia**.
- You want records from the **ISSN Portal**: use **seriatim**.
- You want preprints from **arXiv**: use **archeion**.
- You are building a client for **another scholarly API** in this style:
  build on **bibliofabric**. Start with the
  [Building a client guide](bibliofabric/writing-a-client.md) (and the
  [client quick start](bibliofabric/client.md)) covering settings, auth,
  dialects, unwrappers, resource hooks, sync twins, and monorepo registration.
- You want to see **planned API clients and the canonical entity fusion
  architecture**: explore the [Roadmap & Architecture](roadmap/index.md)
  section, including the 2025–2026 academic API catalogs, Wave 1 starter specs,
  and fusion blueprint.

Requires Python 3.12 or newer. See the [contributing guide](contributing.md)
to set up the workspace and run the test and lint gates.
