# bibliofabric

Async and sync Python client libraries for scholarly metadata APIs, in one uv
workspace. The [`bibliofabric`](https://pypi.org/project/bibliofabric/) core
owns HTTP with retries and rate limiting, authentication, error mapping,
paging, batch retrieval, identifier normalization, and typed resource
clients. Three libraries build on it, one per API.

| Package | API | Version | Docs |
|---|---|---|---|
| [bibliofabric](packages/bibliofabric/README.md) | core framework (no API) | [0.7.0](https://pypi.org/project/bibliofabric/) | [docs](https://utsmok.github.io/bibliofabric/bibliofabric/) |
| [aireloom](packages/aireloom/README.md) | OpenAIRE Graph API (V4), Scholexplorer | [0.9.0](https://pypi.org/project/aireloom/) | [docs](https://utsmok.github.io/bibliofabric/aireloom/) |
| [aletheca](packages/aletheca/README.md) | OpenAlex | [0.5.0](https://pypi.org/project/aletheca/) | [docs](https://utsmok.github.io/bibliofabric/aletheca/) |
| [stavrophora](packages/stavrophora/README.md) | Crossref REST API | [0.4.0](https://pypi.org/project/stavrophora/) | [docs](https://utsmok.github.io/bibliofabric/stavrophora/) |

```bash
uv add aireloom    # or aletheca, stavrophora, bibliofabric
```

Requires Python 3.12 or newer. All four packages ship async clients alongside
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
uv run pytest                                       # all four test suites (live tests deselected)
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
