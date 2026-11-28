# Records

The record summary route (`GET /{orcid}/record`) returns everything public in one document: the ORCID identifier, preferences, history, the person section, and the activities summary. `client.record.get()` validates it into `OrchisRecord`.

```python
record = await client.record.get("0000-0002-1694-233X")

print(record.orcid_identifier.uri)  # https://orcid.org/0000-0002-1694-233X
print(record.history.creation_method)  # WEBSITE
print(record.history.claimed)  # True
print(record.person.name.given_names.text)  # Thomas B.
works = record.activities_summary.works
print(works.put_codes()[:5])
```

The identifier input is normalized: `https://orcid.org/0000-0002-1694-233X`, the compact form, and the bare hyphenated iD all work. `client.record.exists(orcid)` sends `GET` and returns `False` on 404.

## Sections

`record.person` holds the full person section and `record.activities_summary` holds every activity section as it stood with the record. A section the record does not use is `None`. For fresh data, fetch the sections through `client.person` and `client.activities`, which hit their own routes.

## Other representations

The API answers XML for the same route with `Accept: application/xml` (and with no `Accept` header at all). `client.record.representation(orcid)` returns that body as text:

```python
xml = await client.record.representation("0000-0002-1694-233X")
print(xml[:200])
```

`application/ld+json` answers 406 on the public API as of 2026-11-27, so no JSON-LD method exists.

## Values

ORCID wraps almost every scalar as `{"value": ...}`. The models expose wrapped text through the `text` property, and the module-level `text()` helper accepts any wrapper or `None`:

```python
from orchis import text

print(record.person.name.credit_name)  # TextValue model or None
print(record.person.name.credit_name.text)  # unwrapped string or None
print(text(record.person.name.credit_name))  # same
```

Dates such as `{"year": {"value": "2020"}}` validate into `FuzzyDate`, whose `iso()` returns `2020`, `2020-06`, or `2020-06-15` depending on the parts the record carries.
