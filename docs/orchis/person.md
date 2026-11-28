# Person

The person section (`GET /{orcid}/person`) holds the name, other names, biography, researcher URLs, emails, addresses, keywords, and external identifiers. `client.person.get(orcid)` validates it into `Person`; each part also has its own route.

| Method | Route | Notes |
|---|---|---|
| `personal_details(orcid)` | `/{orcid}/personal-details` | name, other names, biography |
| `biography(orcid)` | `/{orcid}/biography` | `None` when the record has none |
| `researcher_urls(orcid)` | `/{orcid}/researcher-urls` | |
| `emails(orcid)` | `/{orcid}/emails` | `None` when the record has none |
| `addresses(orcid)` | `/{orcid}/address` | two-letter countries |
| `keywords(orcid)` | `/{orcid}/keywords` | |
| `external_identifiers(orcid)` | `/{orcid}/external-identifiers` | Scopus, ISNI, and so on |

```python
person = await client.person.get("0000-0002-1694-233X")
print(person.name.family_name.text)  # Hickey
print([name.content for name in person.other_names.other_name])

urls = await client.person.researcher_urls("0000-0002-1694-233X")
for url in urls.researcher_url:
    print(url.url_name, url.url.text)

biography = await client.person.biography("0000-0002-1694-233X")
# None: this record has no biography (the API answers 404 with error code 9041)
```

Every element carries `put-code`, `path`, `visibility`, and its `source`, so you can tell a researcher-asserted claim from one imported by a client (`source.source_client_id`).

Names differ between sections: the person section uses `given-names` and `family-name` (singular), while expanded search uses `given-names` and `family-names` (plural). The models follow the API spelling, aliased to snake_case attributes.
