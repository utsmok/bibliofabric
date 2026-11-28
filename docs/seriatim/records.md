# ISSN and ISSN-L records

The Portal serves one JSON-LD node per record at
`https://portal.issn.org/resource/ISSN/{issn}` and
`https://portal.issn.org/resource/ISSN-L/{issn}`. The node arrives through
content negotiation with the `Accept: application/ld+json` header, which the
client sends on every request.

```python
record = await client.records.get("0028-0836")
```

Identifiers travel in any spelling the helpers accept. The compact form
`00280836` and URL forms such as
`https://portal.issn.org/resource/ISSN/0028-0836` normalize to `0028-0836`.
A value that fails the check digit raises `ConfigurationError` before a
request leaves the process. A valid but unregistered ISSN raises
`NotFoundError`; the Portal answers those with a 404 and a JSON error body.

## Record fields

`SeriatimRecord` models the fields the Portal publishes today. Every model
allows extra keys, so new fields stay reachable as model extras, and
`record.raw` holds the untouched node.

| Field | JSON key | Content |
|---|---|---|
| `issn`, `issn_l`, `key_title` | `identifiedBy` | Properties that read the `#ISSN`, `#ISSN-L` and `#KeyTitle` nodes |
| `format` | `format` | `medium:Print` or `medium:Online` |
| `type` | `type` | The `bf:Work`, `bf:Instance`, `schema:Periodical` set |
| `type_dct` | `typeDct` | The DCT form-of-material code, for example `formofmaterial:a` |
| `main_title`, `name`, `alternate_name`, `title` | same keys | Title variants; `title` mixes id references and language-tagged title objects |
| `identified_by` | `identifiedBy` | The identifier nodes, including `hasCancelledISSN` lists |
| `is_part_of` | `isPartOf` | Cluster memberships with ISSN-L and ISSN-H links |
| `spatial` | `spatial` | Country URIs |
| `url` | `url` | Access URLs |
| `has_cancelled_issn_l`, `has_incorrect_issn` | `hasCancelledISSN-L`, `hasIncorrectISSN` | Related ISSN lists |
| `main_entity_of` | `mainEntityOf` | Record status, modification date, ISSN centre attribution, creation activity |

Cancelled records answer a much smaller node with `@context`, `id`,
`identifiedBy` and `mainEntityOf` only. The flat identifier node then
carries `cancelledInFavorOf` and the status `idStatus:Cancelled`; the same
model covers both shapes, and `record.issn` works for both.

```python
cancelled = await client.records.get("0302-2889")
print(cancelled.issn)  # 0302-2889
print(cancelled.main_entity_of.status)  # recordStatus:Cancelled
```

## Raw node access

```python
node = await client.records.raw("0028-0836")
print(node["mainEntityOf"]["modified"])
```

`raw` returns the parsed JSON object as sent. Use it when the Portal
publishes a field that the model does not carry yet.

## ISSN-L clusters

`client.issn_l` takes an ISSN value and returns the cluster node. The
`hasPart` array lists every medium that shares the ISSN-L, print and online
alike, each with its `identifier` and `format`.

```python
cluster = await client.issn_l.get("0028-0836")
for part in cluster.has_part:
    print(part.identifier, part.format)
```

## The ISSN-L table

The ISSN Centre publishes the whole ISSN to ISSN-L mapping as a zip at
`/public/issnltables.zip` (about 27 MB zipped and 2.6 million ISSNs on
2026-11-28). `client.issn_l.download_table()` streams it to a file, and two
readers stream its members without unpacking the zip.

```python
from seriatim import iter_issn_l_clusters, iter_issn_to_issn_l

path = await client.issn_l.download_table("issnltables.zip")
for link in iter_issn_to_issn_l(path):
    link.issn, link.issn_l, link.medium  # "0028-0836", "0028-0836", "ta"
for issn_l, issns in iter_issn_l_clusters(path):
    ...
```

`iter_issn_to_issn_l()` yields one `IssnLink` per ISSN. Its `medium` comes
from a third column that the readme of the zip does not mention; the values
are the medium codes of MARC 21 field 007, positions 00 and 01 (`ta` printed
text, `cr` online resource, `co` optical disc). `iter_issn_l_clusters()`
yields each ISSN-L with every ISSN that links to it, the ISSN-L included.

## Existence checks

`client.records.exists(issn)` performs a `GET` and returns `False` on 404.
Check-digit failures never reach the network; they raise
`ConfigurationError`.
