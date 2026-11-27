# Crossref quirks

Behavior of the live API that shapes how the client works. Each item is verified against the live service.

## Filters

- `filter=doi:a|b` returns zero results. The supported OR form is repeated keys: `filter=doi:a,doi:b`. Batch lookups use that form.
- Crossref has no publisher filter. Scope by `prefix`, `member`, or `ror-id` instead.
- Unknown query parameters are rejected with 400, not ignored. The client sends only `rows`, `offset`, `query`, `filter`, `sort`, `order`, `select`, `cursor`, and `mailto`, and rejects per-route unsupported ones client-side.

## Paging

- There is no `page` parameter. Paging is `offset` plus `rows`, with `offset + rows <= 10000` and `rows <= 1000`. `search()` raises `ConfigurationError` before sending a request past the cap.
- Deep paging uses `cursor` on `/works` and scoped `*/works` routes; non-works list routes (`/journals`, `/funders`, `/members`, `/licenses`) reject `cursor` with 400 and use offset paging instead. Cursor exhaustion is implicit: the last non-empty page still returns a `next-cursor`; only the following request returns empty `items`.
- Cursor requests reject the `issued` and `published*` sorts with a `sort-criteria-incompatible-with-cursor` 400 (since 2026-08-24). Cursor result sets are no longer stable under index-date windows, so incremental sync should prefer `from-created-date` / `until-created-date` windows over `from-index-date`.
- `sample` caps at 100 and cannot combine with `rows` or `offset`; `sample()` handles both.
- The API serves both `https://api.crossref.org` and `https://api.crossref.org/v1` with identical payloads; stavrophora pins `/v1`.

## Routes

- `/prefixes` has no list route (404); only `/prefixes/{prefix}` and `/prefixes/{prefix}/works` exist. `/licenses` has no single-item route (404); only the list exists.
- `/types` ignores `rows` and `offset` and always returns the complete list (about 30 types).
- `/journals/{issn}` returns `title` as a bare string while `/journals` returns a list; the `Journal` model accepts both.
- `/prefixes/{prefix}` returns `member` and `prefix` as full `https://id.crossref.org/member/297`-style URIs; the `Prefix` model normalizes them to bare values.

## Response shapes

- Every response wraps in one `message` level: single items live in `message`, lists in `message.items` with totals in `message.total-results`. `Page.meta` carries the envelope minus the results, so facets and totals stay reachable.
- The published spec is incomplete: several returned fields are absent from it. All models use `extra="allow"`, so unknown fields survive parsing.
- Reference entries, license entries, and funder entries vary in shape between publishers; every field is optional and tolerant types (`SafeList`, `SafeStr`, `SafeInt`) absorb nulls and scalar-vs-list differences.
- `event.sponsor` is a string for one sponsor and a list for several (ACM GECCO proceedings print two sponsors). The `Event` model accepts both and always yields a list.
