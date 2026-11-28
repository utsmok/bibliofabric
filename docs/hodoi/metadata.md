# Metadata

Content negotiation turns a plain DOI URL into a metadata endpoint. Send an `Accept` header to `GET https://doi.org/{doi}`, and the resolver redirects to the data server of the registration agency, which answers the metadata in the requested format. `client.content()` sends the request, follows the redirect, and parses the answer.

```python
from hodoi import BIBTEX, CSL_JSON, HodoiClient

async with HodoiClient() as client:
    item = await client.content("10.1038/nature12373", CSL_JSON)
    print(item.title, item.container_title)

    bib = await client.content("10.1038/nature12373", BIBTEX)
    print(bib)
```

## The media type catalog

Import the strings from `hodoi.media_types` instead of typing them by hand:

| Constant | Media type | Crossref | DataCite | mEDRA |
|---|---|---|---|---|
| `CSL_JSON` | `application/vnd.citationstyles.csl+json` | yes | yes | yes |
| `DATACITE_JSON` | `application/vnd.datacite.datacite+json` | no | yes | no |
| `DATACITE_XML` | `application/vnd.datacite.datacite+xml` | no | yes | no |
| `SCHEMAORG_JSONLD` | `application/vnd.schemaorg.ld+json` | no | yes | no |
| `UNIXREF_XML` | `application/vnd.crossref.unixref+xml` | yes | no | no |
| `UNIXSD_XML` | `application/vnd.crossref.unixsd+xml` | yes | no | no |
| `ONIX_DOI_XML` | `application/vnd.medra.onixdoi+xml` | no | no | yes |
| `BIBTEX` | `application/x-bibtex` | yes | yes | yes |
| `RIS` | `application/x-research-info-systems` | yes | yes | yes |
| `BIBLIOGRAPHY` | `text/x-bibliography` | yes | yes | yes |
| `RDF_XML` | `application/rdf+xml` | yes | no | yes |
| `TURTLE` | `text/turtle` | yes | no | yes |

`AGENCY_SUPPORT` carries the same matrix as data. The matrix was checked against one DOI of each agency on 2026-11-28. It differs from the table of the DOI Foundation page for RIS and for the two RDF formats. See [upstream quirks](upstream-quirks.md#content-negotiation).

Requesting a type the agency does not serve raises `APIError` with the agency's error body, for example a DataCite DOI with `UNIXREF_XML` or a Crossref DOI with `SCHEMAORG_JSONLD`. The status is 406 in most cases.

## Parsed and text representations

`content()` parses the three JSON media types into models. `CSL_JSON` becomes a `CslItem`, `DATACITE_JSON` a `DataciteRecord`, and `SCHEMAORG_JSONLD` a `SchemaOrgThing`. Each model pins the identity fields and allows every other field through, because all three schemas are large and open. Every other media type returns its text unchanged (BibTeX, RIS, the XML dialects, formatted citations).

A media type may carry parameters. The client reads the type before the semicolon, so `f"{CSL_JSON}; charset=utf-8"` parses like `CSL_JSON`.

When the agency answers HTTP 204, `content()` returns `None`.

## The un-parsed bytes

`raw()` returns the bytes of the answer instead of a model or text. With the default setting it returns the body of the resolver's 302, a small HTML page titled "Handle Redirect" that links to the data server of the agency. The method returns bytes only. To read the `Location` header of the redirect, call `resolve()`.

Pass `follow_redirects=True` to receive the bytes of the metadata itself:

```python
payload = await client.raw("10.1038/nature12373", CSL_JSON)  # body of the 302
payload = await client.raw(
    "10.1038/nature12373", CSL_JSON, follow_redirects=True
)  # CSL JSON bytes
```

The `HODOI_FOLLOW_REDIRECTS` setting is off by default. `content()` always follows the redirect, and `raw()` follows it only when the setting is on or you pass `follow_redirects=True`.

## Reference pages

- DOI Foundation, [DOI content negotiation](https://citation.doi.org/docs.html): the format matrix and response codes.
- Crossref, [Content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/): the Crossref formats and how the resolver redirects to the `/transform` route.
- mEDRA answers content negotiation from its own server, `data.medra.org`. The DOI Foundation page documents its ONIX for DOI type.
