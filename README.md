# bibliofabric

Async and sync Python client libraries for scholarly metadata APIs, in one uv
workspace. The [`bibliofabric`](https://pypi.org/project/bibliofabric/) core
owns HTTP with retries and rate limiting, authentication, error mapping,
paging, batch retrieval, identifier normalization, and typed resource
clients. Three libraries build on it, one per API, and eleven more Wave 1
libraries are built in this workspace and wait for their first release.

| Package | API | Version | Docs |
|---|---|---|---|
| [bibliofabric](packages/bibliofabric/README.md) | core framework (no API) | [0.8.0](https://pypi.org/project/bibliofabric/) | [docs](https://utsmok.github.io/bibliofabric/bibliofabric/) |
| [aireloom](packages/aireloom/README.md) | OpenAIRE Graph API (V4), Scholexplorer | [0.9.1](https://pypi.org/project/aireloom/) | [docs](https://utsmok.github.io/bibliofabric/aireloom/) |
| [aletheca](packages/aletheca/README.md) | OpenAlex | [0.5.1](https://pypi.org/project/aletheca/) | [docs](https://utsmok.github.io/bibliofabric/aletheca/) |
| [stavrophora](packages/stavrophora/README.md) | Crossref REST API | [0.5.0](https://pypi.org/project/stavrophora/) | [docs](https://utsmok.github.io/bibliofabric/stavrophora/) |

The eleven Wave 1 packages are complete and tested but not yet published on
PyPI, so they install from this workspace only. The
[Wave 1 roster](docs/roadmap/wave-1-libraries.md) lists each one with its
upstream API, and the [deferred list](docs/roadmap/deferred.md) records what
each one leaves out.

| Package | API | Version | Docs |
|---|---|---|---|
| [rorifer](packages/rorifer/README.md) | ROR (research organizations and funders) | [0.1.0](packages/rorifer/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/rorifer/) |
| [zenotheca](packages/zenotheca/README.md) | Zenodo REST API and OAI-PMH | [0.1.0](packages/zenotheca/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/zenotheca/) |
| [dataphora](packages/dataphora/README.md) | DataCite REST API and public GraphQL | [0.1.0](packages/dataphora/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/dataphora/) |
| [opcitato](packages/opcitato/README.md) | OpenCitations Index and Meta APIs | [0.1.0](packages/opcitato/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/opcitato/) |
| [hodoi](packages/hodoi/README.md) | DOI registration agency lookup, content negotiation, and Handle records | [0.1.0](packages/hodoi/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/hodoi/) |
| [scholiast](packages/scholiast/README.md) | Semantic Scholar Graph, Recommendations, and Datasets APIs | [0.1.0](packages/scholiast/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/scholiast/) |
| [orchis](packages/orchis/README.md) | ORCID Public API v3.0 | [0.1.0](packages/orchis/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/orchis/) |
| [europaea](packages/europaea/README.md) | Europe PMC REST web services and annotations API | [0.1.0](packages/europaea/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/europaea/) |
| [quiddita](packages/quiddita/README.md) | Wikidata (action API, REST API, and SPARQL) | [0.1.0](packages/quiddita/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/quiddita/) |
| [diurnalia](packages/diurnalia/README.md) | DOAJ (open access journals and articles) | [0.1.0](packages/diurnalia/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/diurnalia/) |
| [seriatim](packages/seriatim/README.md) | ISSN Portal | [0.1.0](packages/seriatim/CHANGELOG.md), not published | [docs](https://utsmok.github.io/bibliofabric/seriatim/) |

```bash
uv add aireloom    # or aletheca, stavrophora, bibliofabric
```

Requires Python 3.12 or newer. Every package ships async clients alongside
generated sync twins (`<Name>SyncClient`, generated from `_async/` by
`scripts/unasync.py`), plus `py.typed`.

## Workspace layout

```
packages/<name>/    one package each: src/, tests/, pyproject.toml, README, CHANGELOG
scripts/            code generation (scripts/unasync.py generates _sync/ twins)
docs/               one mkdocs site for the whole family (docs/<name>/)
archive/            historical documents from the former standalone repos
.github/workflows/  one CI pipeline: lint, test matrix, docs, tag-driven publish
```

Tooling (ruff, ty, pytest, mkdocs) is configured once at the root. From the
repository root:

```bash
uv sync --all-packages --all-groups                 # install all packages plus dev/docs groups
uv run pytest                                       # every test suite (live tests deselected)
uv run ruff check                                   # lint every package and scripts/
uv run ty check packages/*/src packages/*/tests scripts/unasync.py  # type gate
uv run python scripts/unasync.py --check            # verify generated _sync/ twins are fresh
uv run mkdocs serve                                 # docs preview for the whole family
```

Releases are tag-driven: push a tag `<package>-v<version>` (for example
`aletheca-v0.4.1`) and CI builds, publishes that package to PyPI, and creates a
GitHub Release. See [docs/contributing.md](docs/contributing.md) for
contributing and [AGENTS.md](AGENTS.md) for release details and agent
guidelines.
