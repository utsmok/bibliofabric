# Projects, organizations, data sources, persons

These four resources share the research-product machinery: one V4 `filter`
expression, the same `search`/`iterate`/`count` helpers, and V3 by-id
lookups. They differ in filter fields, sort fields, and models.

```python
from aireloom import (
    DataSourcesFilters,
    OrganizationsFilters,
    PersonsFilters,
    ProjectsFilters,
)

page = await client.projects.search(
    ProjectsFilters(funder="EC", project_status="ongoing"), page_size=25
)
org = await client.organizations.get("wtso__________::1234")
sources = await client.data_sources.search(
    DataSourcesFilters(jurisdiction="Governmental"), page_size=10
)
persons = await client.persons.search(
    PersonsFilters(given_name="Ada", last_name="Lovelace")
)
```

## Sort fields

Only these fields sort. Anything else raises `ConfigurationError` before a
request is sent:

- research products: `relevance`, `publication_date`, `date_of_collection`,
  `citation_count`, `influence`, `popularity`, `impulse`
- projects, organizations, data sources, persons: `relevance`

Directions are `asc`/`desc`; the default direction depends on the field.
`sort="relevance"` sorts by match score for free-text queries.

## Valid filter fields

The filter models list exactly the fields the V4 endpoints accept; extra
attributes are rejected by pydantic. The dotted aliases mirror the API
field names (`organizations.id`, `compatibility.name`,
`collected_from.id`). Unknown V4 fields raise a server-side error, which is
how the models stay honest.

## Counts and aggregations

```python
n = await client.projects.count()
by_status = await client.projects.group_by("project_status")
facets = await client.organizations.facets("country", page_size=1)
```

## Organization name variants

```python
orgs = await client.organizations.find_variants(
    ["universiteit twente", "university of twente"], country="NL"
)
```

Each fragment becomes one free-text search; results are deduplicated by
exact `id`, keeping the first occurrence. Records with `pending_org_::`
identifiers are kept on purpose: they carry organization-project links
that the canonical merged record lost, which makes them the main source
of undercounted org-project links. Merging them is the caller's decision.
