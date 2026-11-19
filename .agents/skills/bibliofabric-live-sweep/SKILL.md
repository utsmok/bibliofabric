---
hide: true
name: bibliofabric-live-sweep
description: "Live-verify a bibliofabric-family API client package (aletheca/AIREloom/stavrophora/siblings in the utsmok/bibliofabric monorepo): persist-then-parse evidence, all endpoints, raw-vs-parsed compares, fix bugs in the owning package"
---

Procedure for live-verifying a bibliofabric-family client package
(packages/aletheca, packages/aireloom, packages/stavrophora, future siblings)
against its real API. Use when a client is newly built, its upstream API
changed, or the owner asks for "live pulls of all endpoints with correct
parsing".

## Ground rules
- One package per sweep; never touch other packages in the same sweep. Fixes land in the owning package as regression tests + family-style commits (short imperative, no AI attribution).
- Request budget: 40-66 requests, planned up front. Polite credentials always (mailto / service creds). Polite rate limits are low — serialize and stay under.
- `uv` may be missing from PATH: use `$HOME/.local/bin/uv`. From the repo root: `uv sync --all-packages --all-groups`; run the mocked gate first (`uv run pytest packages/<pkg>/tests`) so live failures aren't drowning in known ones.

## Persist-then-parse (mandatory)
Write EVERY raw payload to `/tmp/<client>_sweep_artifacts/` (plus a `requests.jsonl` log) immediately on receipt, before any parsing or post-processing. A report-stage crash must not destroy evidence (this exact failure happened once). If evidence is still lost, refetch is cheap for single-entity gets — ask the coordinator, don't silently skip field-compares.

## Sweep shape
- Every resource × its supported ops: get / search / list; designed-to-raise ops (e.g. stavrophora `prefixes.search`) are asserted to raise without an HTTP call.
- Scoped sub-resources (`journals.works(issn)`, `funders.works(id)`, `prefixes.works(prefix)`) with a scope-membership assertion.
- Boundary tests: batch splits at its documented limit (stavrophora batch_get_by_doi: 50 keys → 51 inputs = exactly 2 requests); cursor iteration 3 pages with a no-duplicate assertion.
- Family convention: `get()` returns the unwrapped model, `search()` returns a `Page[E]` envelope — script accordingly.

## Evidence standard
- Raw-vs-parsed compare for the richest models: one record fetched via httpx direct AND via the client, ~5 documented fields each, plus `extra="allow"` unknown-key absorption and SafeStr/SafeList coercion checks (null list → [], nulls stripped, None preserved).
- Validate reported "misses" raw before believing them (dead DOIs / unregistered ids return 404 — not client bugs).
