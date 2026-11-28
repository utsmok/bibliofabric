# Events

The `events` resource reads the [citation, reference, view, and download event log](https://support.datacite.org/reference/get_events.md) that DataCite feeds from DOI landing pages and Content Negotiation. Events are write-once records with no update or delete.

```python
from dataphora import EventFilters

page = await client.events.search(
    EventFilters(doi="10.5438/0012", citation_type="journal-article"),
    page_size=100,
)
event = page.results[0]
event.subj_id  # landing page or DOI the event happened on
event.obj_id  # target of a citation or reference
event.relation_type_id  # "is-referenced-by", "is-cited-by", "views", ...
event.occurred_at  # None on older records, which carry occured_at instead
event.source_id  # "datacite-crossref", "datacite-usage", ...
event.total
event.relationships["subj"].data.id
page.meta["facets"]
```

Attribute aliases mirror the upstream hyphenated names (`subj-id`,
`obj-id`, `relation-type-id`, `source-id`, `message-action`,
`source-token`). The date exists under two spellings: older records carry
the spec spelling `occured-at` and recent records carry `occurred-at`, so
the model has the two fields `occured_at` and `occurred_at`.

## Always pass a filter

The unfiltered `/events` route walks the full history and stalls for tens of
seconds. Give the search at least one criterion, for example `doi=`,
`source-id=`, or `relation-type-id=`.

## Counting by facet

```python
page = await client.events.search(
    EventFilters(doi="10.5438/0012"),
    page_size=1,
)
page.meta["citation-count"]  # total citation count
page.meta["facets"]["relation-type-id"]
page.meta["facets"]["source"]
```

With `page_size=1` the envelope `meta` answers "how many and of what kind"
in one request; `count()` returns the plain number.
