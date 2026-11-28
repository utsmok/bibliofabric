# Claims and statements

Wikidata serves statements in two shapes. The Action API shape lives in `client.entities` and `client.claims`; the REST shape lives in `client.statements`.

## `wbgetclaims` (Action API)

```python
claims = await client.claims.get("Q42", property="P569", rank="preferred")
claim = claims["P569"][0]
print(claim.mainsnak.datavalue.value)  # the raw Wikidata value shape
print(claim.qualifiers, claim.references)
```

`get()` returns a `ClaimsByProperty` dict keyed by property id. `rank` accepts `"deprecated"`, `"normal"`, and `"preferred"`; other values are rejected locally because the API would answer `badvalue`. Each claim is a `Claim` model with `mainsnak`, `rank`, `qualifiers` (dict of property id to `Snak`), and `references`.

## REST statements

```python
statements = await client.statements.for_entity("Q42", property="P31")
statement = statements["P31"][0]
print(statement.value.content)  # the typed REST content
print(statement.qualifiers, statement.references)

statement = await client.statements.get("Q42$F078E5B3-F9A8-480E-B7AC-D97778CBBEF9")
```

`for_entity()` accepts item and property ids and returns a `StatementsByProperty` dict. `get()` fetches one statement by its id (the `$` is URL-encoded). REST qualifiers and references are `RestQualifier` records whose `property` is a `{id, data_type}` object and whose `value` is a `{type, content}` object; `content` is `None` for `somevalue` and `novalue` snaks.
