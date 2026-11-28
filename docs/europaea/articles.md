# Articles

`client.articles` covers the article record and its sibling routes. Combined
ids use the `SOURCE:ID` form (`MED:23903748`, `PMC:PMC4221854`, `PPR:...`).

## One record

```python
article = await client.articles.get("MED:23903748")
print(article.title, article.cited_by_count)
print(article.journal_info.journal.title)
print(article.author_list.author[0].author_id.value)  # ORCID

found = await client.articles.exists("MED:23903748")
```

`get()` requests `resultType=core` and raises `NotFoundError` for an unknown
id. `exists()` sends `GET`, because the gateway answers `HEAD` with 405.

## Full text and supplementary files

```python
document = await client.articles.full_text_xml("PMC13810549")
print(document.xml[:200])  # JATS article XML as text

book = await client.articles.book_xml("NBK32884")
if book.message:
    print(book.message, book.is_open_access)

bundle = await client.articles.supplementary_files("PMC13810549")
# bytes of a ZIP archive
```

`full_text_xml` and `book_xml` return an `XmlDocument` wrapper around the
answer text; typed JATS parsing is out of scope. Both routes answer 404 for
articles without open access full text, and the book route answers HTTP 200
with a wrapper document (its `message` and `isOpenAccess` land on the model)
when the id is valid but not open access. `supplementary_files` returns the
raw ZIP archive bytes; pass `include_inline_image=True` to add the inline
images.

## References and citations

Both routes page with `page` and `pageSize` and return `Citation` models
with `total` set to the list size of the article.

```python
references = await client.articles.references("MED:23903748", page=1, page_size=25)
citations = await client.articles.citations("MED:23903748", page=1, page_size=25)
print(references.total, citations.total)
```

## Links

```python
db_links = await client.articles.database_links("MED:23903748", page_size=25)

data_links = await client.articles.data_links("MED:23903748")
category = data_links.data_link_list.category[0]
print(category.name, category.category_link_count)
link = category.section[0].linklist.link[0]
print(link.target.title, link.relationship_type.name)

labs = await client.articles.labs_links("MED:23903748")
for provider in labs.links_count_list.provider:
    print(provider.provider_name, provider.links_count)
```

`database_links` returns the curated cross-references as paged
`DatabaseLink` records. `data_links` returns one envelope of `Category`
entries (Altmetric, BioStudies, and others) with the link records inside;
`category` and `obtained_by` narrow it. `labs_links` returns per-provider
link counts.

## Status updates

```python
response = await client.articles.status_updates(["PPR:PPR324115", "MED:23903748"])
print(response.metrics.articles_with_status_update)
for article in response.articles_with_status_update or []:
    print(article.ext_id, article.status_updates)
```

This is the article status monitor (`POST /status-update-search`): it
reports the status changes Europe PMC recorded for the queried articles,
for example preprints that received a published version. Articles without
updates are counted in `metrics` but do not appear in the answer list; only
tracked articles (mostly preprints that later were published in a journal)
carry updates.

## Evaluations

```python
response = await client.articles.evaluations("MED:23903748")
print(response.evaluation_list.evaluation)
```
