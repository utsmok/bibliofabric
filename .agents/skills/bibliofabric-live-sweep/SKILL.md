---
hide: true
name: bibliofabric-live-sweep
description: "Live-verify a bibliofabric-family API client repo (aletheca/AIREloom/stavrophora/siblings): persist-then-parse evidence, all endpoints, raw-vs-parsed compares, fix bugs in the owner repo"
---

Procedure for live-verifying a bibliofabric-family client repo (aletheca, AIREloom, stavrophora, future siblings) against its real API. Use when a client repo is newly built, its upstream API changed, or the owner asks for "live pulls of all endpoints with correct parsing".

## Ground rules
- One repo per sweep; NEVER touch other repos. Fixes land in the client repo as regression tests + family-style commits (short imperative, no AI attribution).
- Request budget: 40-66 requests, planned up front. Polite credentials always (mailto / service creds). Polite rate limits are low — serialize and stay under.
- `uv` may be missing from PATH: use `$HOME/.local/bin/uv`. `uv sync` in the repo; run the mocked gate first so live failures aren't drowning in known ones.

## Persist-then-parse (mandatory)
Write EVERY raw payload to `/tmp/<client>_sweep_artifacts/` (plus a `requests.jsonl` log) immediately on receipt, before any parsing or post-processing. A report-stage crash must not destroy evidence (this exact failure happened once). If evidence is still lost, refetch is cheap for single-entity gets — ask the coordinator, don't silently skip field-compares.

## Sweep shape
- Every resource × its supported ops: get / search / list; designed-to-raise ops (e.g. stavrophora `prefixes.search`) are asserted to raise without an HTTP call.
- Scoped sub-resources (`journals.works(issn)`, `funders.works(id)`, `prefixes.works(prefix)`) with a scope-membership assertion.
- Boundary tests: batch splits at its documented limit (stavrophora batch_get_by_doi: 50 keys → 51 inputs = exactly 2 requests); cursor iteration 3 pages with a no-duplicate assertion.
- Family convention: `get()` returns the unwrapped model, `search()` returns the envelope — script accordingly.

## Evidence standard
- Raw-vs-parsed compare for the richest models: one record fetched via httpx direct AND via the client, ~5 documented fields each, plus `extra="allow"` unknown-key absorption and SafeStr/SafeList coercion checks (null list → [], nulls stripped, None preserved).
- Validate reported "misses" raw before believing them (dead DOIs / unregistered ids return 404 — not client bugs).
- Treat the API's own 400 validation bodies as the authoritative filter/param list (Crossref enumerates all valid filters there). Re-probe documented quirks once each; docs drift happens (Crossref rate-limit docs were stale).

## Triage
Client bug → fix + mocked regression test + commit. API quirk → append to the README quirks section, tiny commit. Never "fix" the API side; never bump versions or publish.

## After fixes
Mocked suite green; if a GitHub remote exists: push, then `gh run watch <run-id> --exit-status` and confirm every job — including any `--cov-fail-under` gate — is green before reporting done. First `mkdocs gh-deploy` push needs Pages enabled: `gh api repos/<owner>/<repo>/pages -X POST -f source='{"branch":"gh-pages","path":"/"}'`.
