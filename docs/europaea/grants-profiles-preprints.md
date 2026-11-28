# Grants, profiles, and preprints

## Grants (the Grist API)

`client.grants` talks to the [grants RESTful (Grist) API](https://europepmc.org/GristAPI), a separate service that holds the grants of the Europe PMC funders.

```python
response = await client.grants.search("malaria", page=1)
print(response.hit_count)  # the API reports it as a string
for record in response.record_list.record:
    print(record.grant.id, record.grant.funder.name, record.person.family_name)

records = await client.grants.iterate("ga:Wellcome Trust", limit=10)  # 10 pages
```

`search` returns the typed `GrantsResponse` envelope; the route pages with
`page` and has no page-size parameter. `iterate` walks pages until the
record list empties, bounded by `limit` pages when given. Grist wants the
parameters glued to the query path (`get/query=malaria&format=json&page=1`);
the client builds that URL.

## Profiles

```python
response = await client.profiles.profile('AUTH:"Kucsko G"')
for source in response.profile_list.source:
    print(source.name, source.count)
```

`profile` is one request, not paged: it reports the article counts per
source (`MED`, `PMC`, `PPR`, and others), publication type, and subset for a
query. `profile_type` accepts `all`, `lite`, or `core`; `synonym=True`
expands MeSH synonyms.

## Preprints

Europe PMC indexes preprints under the `PPR` source. `client.preprints` is
the search resource scoped to that source: it wraps every query in
`SRC:PPR AND (...)`.

```python
page = await client.preprints.search(query="nanodiamond", page_size=25)
print(page.total, page.results[0].source)  # PPR

async for record in client.preprints.iterate(page_size=100):
    print(record.id)
```
