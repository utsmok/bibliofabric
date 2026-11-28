# Utility modules

`client.utilities` wraps the small read modules of the Action API: `wbavailablebadges`, `wbformatentities`, `wbformatvalue`, `wbparsevalue`, `wbsgetsuggestions`, and `wbcheckconstraints`. Parameter facts come from the live study of 2026-11-27 and 2026-11-28; see [upstream quirks](upstream-quirks.md).

## Badges

```python
badges = await client.utilities.available_badges()  # ['Q17437798', ...]
```

`available_badges()` returns every badge id usable on site links.

## HTML formatting

```python
links = await client.utilities.format_entities(["Q42", "P31"])
html = await client.utilities.format_value(
    {"type": "string", "value": "hello"}, "string"
)
```

`format_entities()` returns an HTML `<a>` link per id. The module ignores `props` and `languages` with a warning, so the client does not offer them. `format_value()` takes the `{"type": ..., "value": ...}` datavalue shape; without the `type` key the service answers `baddatavalue`.

## Parsing values

```python
parsed = await client.utilities.parse_value(["Q42"], datatype="wikibase-item")
print(parsed[0].value["id"], parsed[0].type)  # Q42 wikibase-entityid
```

`parse_value()` returns `ParsedValue` records with the `raw` input, the parsed `value`, and the value `type`.

## Property suggestions

```python
suggestions = await client.utilities.suggestions(entity="Q42", limit=10)
suggestions = await client.utilities.suggestions(properties=["P31"])
```

`suggestions()` wraps `wbsgetsuggestions`. The module answers `propertysuggester-wbsgetsuggestions-either-entity-or-properties` without `entity` or `properties`, so the client rejects that case before sending. Each `PropertySuggestion` carries `id`, `url`, `rating`, `label`, and `description`.

## Constraint checks

```python
report = await client.utilities.check_constraints(["Q42"])
checks = report["Q42"]["P3192"][0]
print(checks.mainsnak.results[0].status)
```

`check_constraints()` wraps `wbcheckconstraints`. Its entity parameter is `id` (`entity` and `entityid` answer the `no-data` error, verified 2026-11-28). It returns a report keyed by entity id, then property id, with `CheckedClaim` records per claim; each carries the claim `id` and a `mainsnak` with the constraint check `results` (status, constraint, and message HTML). Pass `claim_ids=`, `constraint_ids=`, or `statuses=` to narrow the check.
