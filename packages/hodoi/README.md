# hodoi: Python client for the DOI System (async and sync)

Samuel Mok -- 2026

`hodoi` is a placeholder name. The package will be renamed before its
first release.

hodoi is a Python client for the DOI System proxy server at
[doi.org](https://www.doi.org), built on
[bibliofabric](https://github.com/utsmok/bibliofabric). It looks up the
registration agency of DOIs, reads the Handle.net record behind a DOI, and
fetches metadata in every representation the content negotiation offers
(CSL JSON, DataCite JSON, schema.org JSON-LD, BibTeX, RIS, Crossref
Unixref XML, and more). It ships an async client and a generated sync twin
with the same API. The proxy needs no credentials.

## Install

```bash
uv add hodoi
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from hodoi import CSL_JSON, HodoiClient


async def main():
    async with HodoiClient() as client:
        answer = await client.agency("10.1038/nature12373")
        print(answer.DOI, answer.RA)  # Crossref

        answers = await client.agencies(["10.5281/zenodo.1238808", "10.1400/56174"])
        print([(a.DOI, a.RA) for a in answers])  # DataCite, mEDRA

        url = await client.landing_url("10.1038/nature12373")
        print(url)  # https://www.nature.com/articles/nature12373

        item = await client.content("10.1038/nature12373", CSL_JSON)
        print(item.title)

        bib = await client.content("10.1038/nature12373", "application/x-bibtex")
        print(bib)


asyncio.run(main())
```

## Sync usage

`HodoiSyncClient` is generated from the async source and behaves the same.
It uses plain `httpx.Client` and never starts or touches an event loop, so
it works in scripts, in Jupyter, in threads, and when called from inside a
running event loop.

```python
from hodoi import HodoiSyncClient, CSL_JSON

with HodoiSyncClient() as client:
    record = client.handle("10.1038/nature12373")
    item = client.content("10.1038/nature12373", CSL_JSON)
```

## What the client covers

- `agencies(dois)`: the `GET /ra/{doi}` lookup for one DOI or a comma
  list, chunked at 100 DOIs per request. Unknown or malformed DOIs come
  back as a `status` answer instead of an error.
- `handle(doi)`: the `GET /api/handles/{doi}` record typed as
  `HandleRecord` (values of type `URL`, `HS_ADMIN`, `HS_ALIAS`, and
  numeric types), with optional `index`, `type`, and `auth` filters.
- `landing_url(doi)`: the `URL` entry of the handle record, without
  fetching the landing page.
- `content(doi, media_type)`: the negotiated representation, following the
  resolver's redirect. JSON media types parse into `CslItem`,
  `DataciteRecord`, or `SchemaOrgThing`; every other media type returns as
  text.
- `raw(doi, media_type)`: the un-parsed bytes. Redirects stay off by
  default, so you can inspect the resolver's 302 body and `Location`.

## Media types

Import the strings from the catalog instead of typing them by hand:
`CSL_JSON`, `DATACITE_JSON`, `DATACITE_XML`, `SCHEMAORG_JSONLD`,
`UNIXREF_XML`, `UNIXSD_XML`, `ONIX_DOI_XML`, `BIBTEX`, `RIS`,
`BIBLIOGRAPHY`, `RDF_XML`, and `TURTLE`. `AGENCY_SUPPORT` records which of
Crossref, DataCite, and mEDRA answer each type; unsupported combinations
answer HTTP 406.

## Rate limiting and etiquette

doi.org publishes no rate limit and asks for polite use. The client
defaults to 2 requests per second, concurrency 2, and a 60 second timeout,
configurable through `HODOI_` environment variables (for example
`HODOI_MAX_REQUESTS_PER_SECOND`).

## Documentation

The docs live in [docs/hodoi/](../../docs/hodoi/index.md): one usage
page per area ([agencies](../../docs/hodoi/agencies.md),
[handles](../../docs/hodoi/handles.md),
[metadata](../../docs/hodoi/metadata.md)), the
[live-verified quirks](../../docs/hodoi/upstream-quirks.md), and the
[API reference](../../docs/hodoi/reference.md).
