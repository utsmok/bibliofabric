# hodoi: Python client for the DOI System (async and sync)

Samuel Mok -- 2026

hodoi is a Python client for the DOI System proxy server at
[doi.org](https://www.doi.org), built on
[bibliofabric](https://github.com/utsmok/bibliofabric). It looks up the
registration agency of DOIs, reads the Handle.net record behind a DOI,
returns the redirect a DOI resolves to, and fetches metadata in every
representation the content negotiation of Crossref, DataCite, and mEDRA
offers (CSL JSON, DataCite JSON, schema.org JSON-LD, BibTeX, RIS, Crossref
Unixref XML, and more). It ships an async client and a generated sync twin
with the same API. The proxy needs no credentials.

The package is not yet published on PyPI. Until the first release, use it
from a checkout of the `bibliofabric` workspace, where `uv sync
--all-packages` installs it together with the `bibliofabric` 0.8 it needs.

## Install

```bash
uv sync --all-packages
```

Run the command from the root of the `bibliofabric` workspace checkout. It
requires Python 3.12 or newer.

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

| Method | Request | Result |
|---|---|---|
| `agencies(dois)` | `GET /ra/{doi}` for one DOI or a comma list, in requests of at most 100 DOIs and 4000 path characters | A list of `AgencyAnswer`. Unknown or malformed DOIs carry a `status` string instead of raising. |
| `handle(doi)` | `GET /api/handles/{doi}`, with optional `index`, `type`, `auth`, and `cert` filters (`index` and `type` take one value or a list) | A `HandleRecord`. |
| `landing_url(doi)` | The handle record, without fetching the landing page | The `URL` entry of the record. |
| `resolve(doi)` | `GET https://doi.org/{doi}` for `text/html`, redirects off | The 302 as an `httpx.Response`; its `Location` header holds the landing page. |
| `locations(doi)` | `GET https://doi.org/{doi}?action=showurls` | A list of `RedirectLocation`, one per URL the proxy could redirect to. |
| `content(doi, media_type)` | `GET https://doi.org/{doi}` with an `Accept` header, redirects followed | A `CslItem`, `DataciteRecord`, or `SchemaOrgThing` for the three JSON media types, text for every other type, and `None` for an HTTP 204 answer. |
| `raw(doi, media_type)` | The same request, redirects off by default | The un-parsed bytes, which are the resolver's 302 body unless you pass `follow_redirects=True`. |

## Media types

Import the strings from the catalog instead of typing them by hand:
`CSL_JSON`, `DATACITE_JSON`, `DATACITE_XML`, `SCHEMAORG_JSONLD`,
`UNIXREF_XML`, `UNIXSD_XML`, `ONIX_DOI_XML`, `BIBTEX`, `RIS`,
`BIBLIOGRAPHY`, `RDF_XML`, and `TURTLE`. `AGENCY_SUPPORT` records which of
Crossref, DataCite, and mEDRA answer each type; the others answer with an
HTTP error (406 in most cases).

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
