# Metadata

Content negotiation turns a plain DOI URL into a metadata endpoint: send an `Accept` header to `GET https://doi.org/{doi}` and the resolver redirects to the registration agency's data server, which answers the metadata in the requested format. `client.content()` sends the request, follows the redirect, and parses the answer.

```python
from hodoi import CSL_JSON, BIBTEX, HodoiClient

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
| `BIBTEX` | `application/x-bibtex` | yes | yes | yes |
| `RIS` | `application/x-research-info-systems` | yes | yes | no |
| `BIBLIOGRAPHY` | `text/x-bibliography` | yes | yes | yes |
| `SCHEMAORG_JSONLD` | `application/vnd.schemaorg.ld+json` | no | yes | no |
| `UNIXREF_XML` | `application/vnd.crossref.unixref+xml` | yes | no | no |
| `UNIXSD_XML` | `application/vnd.crossref.unixsd+xml` | yes | no | no |
| `DATACITE_XML` | `application/vnd.datacite.datacite+xml` | no | yes | no |
| `ONIX_DOI_XML` | `application/vnd.medra.onixdoi+xml` | no | no | yes |
| `RDF_XML` | `application/rdf+xml` | yes | yes | yes |
| `TURTLE` | `text/turtle` | yes | yes | yes |

`AGENCY_SUPPORT` carries the same matrix as data. Requesting a type the agency does not serve raises `APIError` with the agency's HTTP 406 (for example, a DataCite DOI with `UNIXREF_XML`, or a Crossref DOI with `SCHEMAORG_JSONLD`).

## Parsed and text representations

`content()` parses the three JSON media types into models: `CSL_JSON` into `CslItem`, `DATACITE_JSON` into `DataciteRecord`, and `SCHEMAORG_JSONLD` into `SchemaOrgThing`. Each model pins the identity fields and allows every other field through, because all three schemas are large and open. Every other media type returns its text unchanged (BibTeX, RIS, the XML dialects, formatted citations).

`raw()` returns the un-parsed bytes instead. It keeps redirects off by default, so the bytes are the resolver's own 302 body ("Handle Redirect") and you can read the redirect decision before paying for the metadata request. Pass `follow_redirects=True` to get the agency's bytes:

```python
payload = await client.raw("10.1038/nature12373", CSL_JSON)  # 302 body
payload = await client.raw(
    "10.1038/nature12373", CSL_JSON, follow_redirects=True
)  # CSL JSON bytes
```

Redirect behavior follows the `HODOI_FOLLOW_REDIRECTS` setting, which is off by default; `content()` always follows.

## Reference pages

- DOI Foundation, [DOI content negotiation](https://citation.doi.org/docs.html): the format matrix and response codes.
- Crossref, [Content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/): the Crossref formats and how the resolver redirects to the `/transform` route.
- mEDRA serves CSL JSON, BibTeX, and RIS-free set through its own server; the DOI Foundation page documents its ONIX for DOI type.
