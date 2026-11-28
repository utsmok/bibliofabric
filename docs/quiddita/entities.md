# Entities

`client.entities` wraps the `wbgetentities` module of the MediaWiki Action API. It returns one entity, a bounded batch, or an unbounded id list, typed as `Entity`.

## One entity

```python
entity = await client.entities.get("Q42")
entity = await client.entities.get("https://www.wikidata.org/wiki/Q42")  # same
```

The id accepts `Q`, `P`, and `L` ids in any letter case, the wiki URL form, and the entity URL form; anything else raises `ConfigurationError` before a request is sent. Unknown ids raise `NotFoundError`.

Pass entity parts with `select=` (mapped to the API's `props` parameter) and the remaining parameters through `params`:

```python
entity = await client.entities.get(
    "Q42",
    select=["labels", "descriptions"],
    params={"languages": ["en", "nl"], "sitefilter": ["enwiki"], "redirects": "no"},
)
```

`redirects` accepts `"yes"` and `"no"` (default `"yes"`). With `"no"`, a redirect id answers as a stub entity with `info` only.

## Batches

`batch_get()` chunks ids at the API's limit of 50 ids per request and returns a dict keyed by the normalized id. An unknown id raises `NotFoundError` for the whole batch.

```python
batch = await client.entities.batch_get(["Q42", "P31", "L1"], select=["labels"])
```

`batch_get()` inherits the framework's concurrency bound, deduplication, and `on_error="skip"` failure handling.

## Iterating many ids

`iterate_ids()` walks an unbounded id list in order, 50 ids per request:

```python
async for entity in client.entities.iterate_ids(ids, props=["claims"]):
    ...
```

Ids are normalized and deduplicated first. An unknown id raises `NotFoundError`. With `on_error="skip"` the client drops the id, repeats the request without it, and records the id in `failures` with its `NotFoundError`:

```python
failures = []
async for entity in client.entities.iterate_ids(
    ids, on_error="skip", failures=failures
):
    ...
```

## EntityData: the full entity per format

`client.entity_data` reads `wiki/Special:EntityData/{id}.{format}`, which serves the full entity in one serialization without the 50-id limit of `wbgetentities`:

```python
result = await client.entity_data.get("Q42")  # json
print(result.entity.id, result.entity.claims)

ttl = await client.entity_data.get("Q42", format="ttl")
print(ttl.document.content_type, len(ttl.document.text))

old = await client.entity_data.get("Q42", revision=2575435918)  # an old revision
```

`get()` returns an `EntityDataResult`. For `format="json"` the `entity` field carries the parsed `Entity` (the payload is the same shape as `wbgetentities`). For `jsonld`, `rdf`, `nt`, `ttl`, and `n3` the `document` field carries an `EntityDataDocument` with the raw `text` and the answered `content_type`. Other suffixes answer 415, so `format` is validated client-side. `revision=` serves an old revision id; an unknown revision answers 404. An invalid id is rejected client-side.

`negotiate()` walks the content-negotiation route for callers who want it: `https://www.wikidata.org/entity/{id}` answers 303 to `Special:EntityData` based on the `Accept` header, and the client follows the redirect:

```python
document = await client.entity_data.negotiate("Q42", accept="text/turtle")
```

## Models

`Entity` carries `type`, `id`, `labels`, `descriptions`, `aliases`, `claims`, `sitelinks`, `datatype` (properties), and the page metadata (`pageid`, `lastrevid`, `modified`). `Claim` carries `mainsnak`, `rank`, `qualifiers`, and `references`; `Snak.datavalue` keeps the value untyped (`DataValue.value`) so every Wikidata value shape survives. `Sitelink` carries `site`, `title`, `badges`, and `url` when `sitelinks/urls` was requested. Unknown fields are kept (`extra="allow"`), so lexeme payloads survive validation.
