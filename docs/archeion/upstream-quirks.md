# Upstream quirks

Checked against the live API on 2026-11-28.

- A malformed id answers HTTP 400 with an Atom error feed. Its one entry has an `id` that starts with `https://arxiv.org/api/errors` and the reason in `summary`, for example `incorrect id format for bad-id`. A well-formed id that does not exist answers 200 with `totalResults` 0.
- An old-style id with a version (`hep-th/9711200v1`) in `id_list` answers HTTP 500, alone or with other ids. The same id without its version, and new-style ids with a version (`1706.03762v1`), answer 200.
- `id_list` results do not come back in request order: `1706.03762v1,1706.03762` answered v7 first.
- `max_results=3000` answered 3000 entries, although the documentation caps one slice at 2000. The client keeps the documented caps of 2000 per request and 30,000 per query.
- `max_results=0` answers one entry rather than a bare total, so `count()` asks for one result.
- Titles keep the line breaks and indentation of the submission; the parser collapses them to single spaces.
- Responses go through a Google Frontend and Varnish cache (`x-cache` headers) and carry no rate-limit headers. The terms of use ask for one request every three seconds over one connection.
