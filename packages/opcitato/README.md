# opcitato: Python client for the OpenCitations APIs (async and sync)

Samuel Mok -- 2026

opcitato is a Python client for the [OpenCitations Index API
v2](https://opencitations.net/index/api/v2), the [OpenCitations Meta API
v1](https://opencitations.net/meta/api/v1), and the SPARQL endpoint of each
dataset, built on [bibliofabric](https://github.com/utsmok/bibliofabric).
The async client is the source of truth; a generated sync twin
(`OpcitatoSyncClient`, `IndexSyncClient`, `MetaSyncClient`) offers the same
API without an event loop. The APIs need no credentials.

The package is not yet published on PyPI. Until the first release, use it
from a checkout of the `bibliofabric` workspace, where `uv sync
--all-packages` installs it together with the `bibliofabric` 0.8 it needs.

**Docs:** [utsmok.github.io/bibliofabric/opcitato](https://utsmok.github.io/bibliofabric/opcitato/) -- **License:** MIT

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API.
- **Every read operation of both APIs**: Index `citation`, `citations`,
  `references`, `citation_count`, `reference_count`, and
  `venue_citation_count`; Meta `metadata`, `author`, and `editor`.
- **Both SPARQL endpoints**: `sparql()` returns the typed SPARQL 1.1 JSON
  answer, and `sparql_text()` returns the XML, CSV, TSV, Turtle, or
  N-Triples representation.
- **Typed rows**: Pydantic models for citation rows, count rows, and
  bibliographic metadata, with the multi-identifier `citing`/`cited`/`id`
  strings parsed into `(scheme, value)` pairs.
- **Row shaping**: `require`, `filter`, and `sort` parameters with
  client-side validation, and `format="csv"` parsed into the same models.
- **Documented pace**: 3 requests per second by default, matching the
  documented limit of 180 requests per minute per IP address.

## Quick start

```python
import asyncio
from opcitato import OpcitatoClient


async def main():
    async with OpcitatoClient() as client:
        citations = await client.index.citations("doi:10.1108/jd-12-2013-0166")
        print(len(citations), citations[0].oci, citations[0].timespan)
        print(citations[0].cited_identifiers)

        count = await client.index.citation_count("doi:10.1108/jd-12-2013-0166")
        print("incoming citations:", count)

        records = await client.meta.metadata("doi:10.1007/978-1-4020-9632-7")
        print(records[0].title, records[0].pub_date)

        result = await client.index.sparql(
            "SELECT ?ci ?cited WHERE { "
            "?ci <http://purl.org/spar/cito/hasCitedEntity> ?cited } LIMIT 3"
        )
        for row in result.rows():
            print(row["ci"], row["cited"])


asyncio.run(main())
```

Identifiers must carry their scheme prefix (`doi:`, `omid:`, `pmid:`,
`issn:`, `isbn:` on the Index API; Meta metadata also accepts `openalex:`,
`pmid:`, and `pmcid:`). A bare DOI raises `ConfigurationError` before a
request is sent, because the API would answer 400. The client percent-encodes
the identifier for the URL path, so a DOI with `#` or `?` arrives whole. The
Meta `metadata()` operation accepts a list of identifiers and packs them
into one request with the documented `__` separator.

## Row shaping

```python
rows = await client.index.citations(
    "doi:10.1108/jd-12-2013-0166",
    require="creation",
    filter="creation:>2019-12",
    sort="desc(creation)",
)
csv_rows = await client.index.references("doi:10.7717/peerj-cs.421", format="csv")
```

`require` drops rows whose field is empty, `filter` keeps matching rows (a
regular expression, or `=`, `<`, `>` with a value), and `sort` orders them
(`asc(field)` or `desc(field)`). The parameters may repeat. `format="csv"`
asks the server for its CSV representation and parses it into the same
models; the field names are identical in both representations.

### Sync quick start

```python
from opcitato import OpcitatoSyncClient

with OpcitatoSyncClient() as client:
    records = client.meta.author("orcid:0000-0002-8420-0696")
    for record in records:
        print(record.pub_date, record.title)
```

## Settings

`OpcitatoSettings` loads from environment variables prefixed with
`OPCITATO_` and from a `.env` file in the working directory.
`OPCITATO_MAX_REQUESTS_PER_SECOND` (default 3, the documented limit
of 180 requests per minute) and `OPCITATO_MAX_CONCURRENCY`
(default 3) set the request pace. The shared fields of
`bibliofabric.config.BaseApiSettings` also apply, such as
`OPCITATO_TIMEOUT` and `OPCITATO_MAX_RETRIES`.

## Upstream behavior to know

- **No paging**: every operation answers with the complete result of the
  query. For bulk harvesting beyond the rate limit, OpenCitations publishes
  database dumps at download.opencitations.net.
- **Counts travel as strings**: the JSON body is `{"count": "1806"}`; the
  model coerces it to `int`.
- **An unknown identifier is not an error**: row operations answer `[]`. The
  count operations answered a zero row on 2026-11-28, which
  `citation_count()` and friends return as `0`; an empty list, last seen on
  2026-11-27, becomes `None`.
- **Rejected identifiers answer 400 with a plain-text body**, which the
  framework raises as `APIError`; the client catches the common cases
  (bare DOIs, unsupported schemes) before a request is sent.

See [upstream quirks](upstream-quirks.md) for the full list with dates.
