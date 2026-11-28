# Events

The `events` resource reads the [citation, reference, view, and download event log](https://support.datacite.org/reference/get_events.md) that DataCite feeds from DOI landing pages and Content Negotiation. Events are write-once records with no update or delete.

```python
from dataphora import EventFilters

page = await client.events.search(
    EventFilters(doi="10.5438/0012", citation_type="journal-article"),
    page_size=100,
)
event = page.results[0]
event.subjId  # landing page or DOI the event happened on
event.objId  # target of a citation or reference
event.relationTypeId  # "is-referenced-by", "is-cited-by", "views", ...
event.occurredAt
event.sourceId  # "datacite-crossref", "datacite-usage", ...
event.total
event.relationships["subj"].data.id
event.meta["facets"]
```

Attribute aliases mirror the upstream hyphenated names (`subj-id`,
`relation-type-id`, `citation-type`, `source-id`, `message-action`),
including the spec spelling `occured-at`; recent records answer with the
correct spelling `occurred-at`, and both land in the same field.

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
