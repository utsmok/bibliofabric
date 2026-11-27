# Upstream quirks

Behavior of the OpenAIRE and Scholexplorer services that the client works
around or documents. All of these were observed against the live services.

## V4 page_size, offset, and OR-list caps

- `page_size` must be between `1` and `100` (in both offset and cursor modes);
  larger values return HTTP 400.
- Offset-based paging is limited to `offset <= 10,000` (`max_offset=10_000`);
  use cursor paging (`iterate()` or `cursor="*"`) for larger datasets.
- A single V4 filter field accepts at most 50 pipe-separated OR values
  (OpenAIRE Graph 1.6.0+); larger lists return HTTP 400.

AIREloom enforces all three caps client-side (`GRAPH_DIALECT.max_page_size = 100`,
`GRAPH_DIALECT.max_offset = 10_000`, and 50-value OR check raising `ConfigurationError`).

## Scholix V3 `linkProvider` and date-filter limitations

- `/v3/Links` does not declare `linkProvider` and silently ignores it; `/v2/Links`
  filters by `linkProvider` properly. AIREloom routes queries carrying
  `linkProvider` to `/v2/Links` automatically.
- `/v3/Links` accepts `from` and `to` but returns zero rows for every tested
  date value. `/v2/Links` has no `from`/`to` parameters at all and silently
  ignores them (returning unfiltered links). Passing `from_date` or `to_date`
  to Scholix search or iterate methods raises `ConfigurationError` immediately
  so callers never receive silent zero-row or unfiltered results; filter results
  by `link_publication_date` client-side instead, or query Graph V4 research
  products with `from_publication_date` / `to_publication_date`.

## V4 group_by totals are uneven

The V4 `group_by` aggregation mode reports counts per value together with a
header `numFound`, but the numbers come from different aggregation paths and
are not guaranteed to agree; per-value counts can also differ from what a
plain search for that value reports. Treat `group_by` output as a rough
distribution, not an exact breakdown.

## Graph links and Scholix routes silently truncate at 100

On `/v3/research-products/links` and Scholexplorer `/v2/Links` & `/v3/Links`,
a page size of 100 or more silently returns 10 results without an error. The
client caps page sizes for these routes at 99.

## Graph links pages are not pinned

The links route has no cursor or sort, so a page window only makes sense if
the upstream ordering is stable. If the ordering changes between requests,
relations can be skipped or duplicated. The iterator stops on an empty page
or at the reported total, which bounds the walk but cannot prevent shifts.

## V3 by-id routes need raw colons

The `/v3/{entity}/{id}` routes expect `prefix::suffix` identifiers with the
colons unencoded; percent-encoding them returns 404. The client leaves
colons in place.

## V4 group_by responds with an empty result list

In `group_by` mode the API returns the facet counts and an empty
`results` array, even though `numFound` still counts matching records. The
client reads the counts from the `facets` block and ignores the record list.

## Scholexplorer sends no rate-limit headers

There is no 429 feedback to pace against, so the Scholix client
self-throttles to one request per second.
