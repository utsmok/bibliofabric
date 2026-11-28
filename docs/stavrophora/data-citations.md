# Data citations (beta)

`client.data_citations` covers the Crossref Data Citations API at `https://api.crossref.org/beta/datacitations`. Each record links a citing work (`subject`) to a cited dataset, software, or other work (`object`) with a relation type such as `references`. Crossref marks the route as beta: its contents and output format may change.

```python
page = await client.data_citations.search(object_id="10.3886/ICPSR01132.v1", rows=20)
page.total  # 57 on 2026-11-28
citation = page.results[0]
citation.subject.id  # DOI of the citing work
citation.subject.member  # Crossref member of the citing work
citation.object.type  # "dataset"
citation.relation  # "references"
citation.timestamp  # when Crossref added the relationship
```

## Filters

Every filter is optional, and the filters combine with AND.

| Argument | Query parameter | Matches |
|---|---|---|
| `subject_id` | `subject-id` | DOI of the citing work |
| `object_id` | `object-id` | DOI of the cited object |
| `member_id` | `member-id` | Crossref member ID of the citing work |
| `relation` | `relation` | Relation type, for example `references` |
| `from_created_date` | `from-created-date` | Added on or after this date or time |
| `until_created_date` | `until-created-date` | Added on or before this date or time |

The DOI filters accept a bare DOI or a `https://doi.org/` URL and send the DOI in lower case. The date filters take `2025`, `2025-01`, `2025-01-01`, `2025-01-01T12`, or `2025-01-01T12:00`.

## Paging

The route pages by a 0-based page number. `search()` takes `page=` and `rows=` (1 to 1000, default 20), and `page.next_cursor` holds the next page number as a string, or `None` after the last page. `iterate()` follows the pages with 1000 rows each, and `count()` reads the total with one 1-row request.

```python
async for citation in client.data_citations.iterate(
    member_id=78, from_created_date="2026-11"
):
    ...

await client.data_citations.count(relation="references")
```

## Rate limits

The route runs in its own Crossref pool. On 2026-11-28 it answered `x-api-pool: datacitations`, `x-rate-limit: 3`, and `x-concurrency-limit: 3` with and without `mailto`. The client sends these requests in the `datacitations` rate class at 3 requests per second for every credential type; change it through `STAVROPHORA_RATE_LIMITS`.
