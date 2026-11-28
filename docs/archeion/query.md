# Query

`client.query` wraps `GET https://export.arxiv.org/api/query`, the one read route of the arXiv API. Every result is one paper version as an `ArxivEntry`.

## Search

`search()` takes the arXiv search syntax as `query`: field prefixes such as `ti:` (title), `au:` (author), `abs:` (abstract), `cat:` (category), and `all:`, combined with `AND`, `OR`, and `ANDNOT`.

```python
page = await client.query.search(
    "au:maldacena AND cat:hep-th",
    sort_by="submittedDate",
    sort_order="descending",
    start=0,
    page_size=50,
)
page.total  # opensearch:totalResults
```

`sort_by` takes `relevance`, `lastUpdatedDate`, or `submittedDate`, and `sort_order` takes `ascending` or `descending`. `start` is the 0-based offset and `page_size` the `max_results` value. The documentation caps one request at 2000 results and one query at 30,000, and the client raises `ConfigurationError` beyond either cap.

## Iterate

`iterate()` pages through a query up to `limit` or 30,000 results. At the default pace of one request every three seconds, pages of 100 to 2000 results keep a long harvest short.

```python
async for record in client.query.iterate("cat:q-bio.PE", page_size=500, limit=5000):
    record.arxiv_id, record.doi
```

## Look up papers by id

`get()` returns one paper. It accepts new-style ids (`1706.03762`), old-style ids (`hep-th/9711200`), versions (`1706.03762v1`), and the `arXiv:` and `https://arxiv.org/abs/` forms. Without a version the API answers the newest one. An unknown id raises `NotFoundError`.

`batch_get()` sends `id_list` requests of 100 ids and returns a dict keyed by the requested id. An id without a version maps to the newest version, and unknown ids are absent.

```python
found = await client.query.batch_get(["1706.03762v1", "hep-th/9711200", "2501.99999"])
sorted(found)  # ["1706.03762v1", "hep-th/9711200"]
```

arXiv answers HTTP 500 for an old-style id with a version (`hep-th/9711200v1`), so the client raises `ConfigurationError` for such ids before it sends the request.

## The entry model

| Field | Content |
|---|---|
| `id` | The abstract URL of this version, such as `http://arxiv.org/abs/1706.03762v7` |
| `title`, `summary` | Title (line breaks collapsed) and abstract |
| `published`, `updated` | Date of version 1 and of this version |
| `authors` | `ArxivAuthor` with `name` and `affiliations` |
| `categories`, `primary_category` | arXiv category terms |
| `comment`, `journal_ref`, `doi` | Author comment, journal reference, and DOI when given |
| `links` | `ArxivLink` with `href`, `rel`, `type`, and `title` |

The properties `arxiv_id`, `versioned_id`, `version`, `pdf_url`, and `author_names` derive from these fields.
