---
hide: true
name: bibliofabric-family-release
description: "Cut and verify a PyPI release for any package in the bibliofabric monorepo via tag-driven CI, including release-day gotchas: unpinned uvx ty strictness drift, uv cache staleness after publish, pre-commit PATH breakage, main+tag push racing the docs deploy, consumer-repo regression passes"
---

# bibliofabric family release procedure

Cut and verify a PyPI release for any package in `utsmok/bibliofabric`
(packages/bibliofabric, aireloom, aletheca, stavrophora). Tags
`<package>-v<version>` publish that package; a plain `v<version>` tag
publishes bibliofabric. CI runs lint + a test matrix, a publish job
(`uv build --package <pkg>` + `uv publish dist/*` with GitHub environment
`pypi` + OIDC `id-token: write`), and a `release` job creating the GitHub
Release from `packages/<pkg>/CHANGELOG.md` (with `--generate-notes` fallback).

## Sequence

1. Confirm the tree is clean and every fix that should ship is committed AND pushed (a local-only fix tag silently releases without it — happened once; the tag builds the pushed tree, not your working dir).
2. Re-run the CI type gate locally with the tool CI uses: `uv run ty check packages/*/src packages/*/tests scripts/unasync.py` (`ty` is pinned exactly in the root `dev` group, so local and CI agree). Fix findings properly (declare the missing attributes); prefer structural fixes over `# ty: ignore` suppressions.
3. Bump `version` in `packages/<pkg>/pyproject.toml`; add a changelog entry to `packages/<pkg>/CHANGELOG.md`. Commit family style (`chore(release): bump aireloom to X`), push main, then `git tag aireloom-v0.8.1 && git push origin aireloom-v0.8.1`.
4. `gh run watch <run-id> --exit-status`, then verify the release is actually visible: `uv run --no-project python -c "import httpx; print(httpx.get('https://pypi.org/pypi/<pkg>/json').json()['info']['version'])"`.
5. Wheel-content proof for feature releases: `uv cache clean <pkg>`, then `uv run --no-project --with <pkg>==<ver> python -c "..."` in /tmp and introspect the new API surface (signatures/settings fields). Confirms the published wheel — not just the tag — carries the features.

## Release-day gotchas (2026-09-04 session, still true)

- **uv's simple-index cache goes stale after a fresh publish** for minutes: `uv add pkg>=newver` fails with "only <=oldver available" and `--refresh-package` does NOT fix it (revalidation gets a 304 from a stale CDN edge). Fix: `uv cache clean <pkg>`, then add again. If the index is STILL stale after cleaning (can persist alongside a fresh JSON API), bypass the index entirely: pull the wheel URL from `https://pypi.org/pypi/<pkg>/json` (`urls[].url`) and `uv run --no-project --with <direct-wheel-url> python -c "..."` — proves the published artifact without waiting for the index edge.
- **pre-commit hook shims break silently**: the installed hook's templated python path goes stale, and the `command -v pre-commit` fallback needs `~/.local/bin` on PATH — the persistent shell drops it mid-session. Prefix `export PATH="$HOME/.local/bin:$PATH";` on commit chains (or `--no-verify` for trivial release commits; CI re-runs the same gates).
- **A failed-looking `gh run watch` exit may be an API blip** (especially with output redirected) — re-check with `gh run view <id> --json jobs` before diagnosing or re-tagging.
- **Pushing main and the release tag together races the docs deploy**: both events trigger `mkdocs gh-deploy --force` on the same commit; one run wins, the other fails on the gh-pages ref update. The release itself is fine (tag run's publish + docs succeed) — just `gh run rerun <main-run-id> --failed` to green the main branch run. Durable fix shipped 2026-09-05: `concurrency: {group: gh-pages-deploy, cancel-in-progress: false}` on the docs job (still in `ci.yml`).
- **Never re-publish to fix a bad release**: the tag builds whatever commit it points at; delete + re-cut a tag ONLY when the tagged commit itself was wrong and the release never landed.

## Monorepo notes

- Each package keeps its own version and PyPI name; there is no workspace-wide version bump. The root README table lists current versions — update the row you release (or leave it; it is informational).
- Trusted publishing is registered per package name on PyPI, all pointing at `utsmok/bibliofabric` workflow `ci.yml` and environment `pypi`. A new package needs its own pending-publisher entry before its first tag.
- A tag run runs the FULL test matrix, not just the released package — that is intentional (a core change can break clients).
