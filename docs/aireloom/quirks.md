# Upstream quirks

Behavior of the OpenAIRE and Scholexplorer services that the client works
around or documents. All of these were observed against the live services.

## Scholix V3 date filters return zero rows

`/v3/Links` accepts `from` and `to` but returns an empty result for every
value. Queries with `from_date` or `to_date` are routed to `/v2/Links`
automatically, where the date filters work.

## V4 group_by totals are uneven

The V4 `group_by` aggregation mode reports counts per value together with a
header `numFound`, but the numbers come from different aggregation paths and
are not guaranteed to agree; per-value counts can also differ from what a
plain search for that value reports. Treat `group_by` output as a rough
distribution, not an exact breakdown.

## Graph links route silently truncates at 100

On `/v3/research-products/links`, a `pageSize` of 100 or more returns 10
results without an error. The client caps page sizes for this route at 99.

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
