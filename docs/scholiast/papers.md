# Papers

`client.papers` talks to the `/paper` routes and returns `Paper` models.

## Get one paper

```python
paper = await client.papers.get("DOI:10.1038/nature12373")
paper = await client.papers.get("ARXIV:1304.1068")
paper = await client.papers.get("PMID:23903748")
paper = await client.papers.get("CorpusId:4314121")
paper = await client.papers.get("MAG:2159974629")
paper = await client.papers.get("ACL:W12-1905")
paper = await client.papers.get("649def34f8be52c8b66281af98ae884c09aef38b")  # S2 id
found = await client.papers.exists("DOI:10.1038/nature12373")
```

Every documented id form works in the path: a bare S2 paper id, `DOI:`,
`ARXIV:`, `PMID:`, `PMCID:`, `MAG:`, `ACL:`, `PubMedCentral:`,
`CorpusId:`, and `URL:` (percent-encode the URL value). Ids travel
verbatim; the client does not rewrite them. An unknown id raises
`NotFoundError`.

Without `fields` the API answers with `paperId` only. Select fields with
`select=`:

```python
paper = await client.papers.get(
    "DOI:10.1038/nature12373",
    select=["title", "year", "citationCount", "externalIds", "tldr"],
)
```

The API needs a key for `embedding` and `openAccessDoi`; a keyless request
that asks for them answers HTTP 400.

## The paper model

| Field | Content |
|---|---|
| `paperId`, `corpusId` | The Semantic Scholar ids |
| `externalIds` | `ExternalIds` with `DOI`, `ArXiv`, `MAG`, `PubMed`, `PubMedCentral`, `DBLP`, `ACL`, `Medline`, and the integer `CorpusId` |
| `title`, `abstract`, `venue`, `year`, `publicationDate` | Bibliographic fields |
| `publicationVenue` | Normalized venue: `id`, `name`, `type`, `alternate_names`, `url` |
| `referenceCount`, `citationCount`, `influentialCitationCount` | Graph counters |
| `isOpenAccess`, `openAccessPdf`, `openAccessDoi` | Open-access status, the PDF (`url`, `status`, `license`, `disclaimer`), and the DOI |
| `fieldsOfStudy`, `s2FieldsOfStudy` | Field labels and `S2FieldOfStudy` entries (`category`, `source`) |
| `publicationTypes` | Such as `Journal Article`, `Review` |
| `journal` | `name`, `volume`, `pages` |
| `authors` | `Author` stubs (`authorId`, `name`) |
| `citationStyles`, `textAvailability` | Kept permissive; shape varies |
| `tldr` | `Tldr` (`model`, `text`) |
| `embedding` | `Embedding` (`model`, `vector`); needs a key |
| `matchScore` | Set only on a title match |

Fields the API adds later are kept in `model_extra`.

## Search

```python
page = await client.papers.search(
    query="photosynthesis",
    fields=["title", "year", "citationCount"],
    page_size=10,
    page=2,
)
page.total
page.results  # up to 10 Paper records
page.next_cursor  # the next offset as a string, None on the last page
```

`search()`, `iterate()`, `collect()`, `first()`, and `count()` come from
the resource base. `page` and `page_size` map to the API's `offset` and
`limit`; one query reaches at most 10,000 records because the API caps
`offset + limit` at 10,000.

Filters are their own query parameters. Pass them as a model or a mapping:

```python
from scholiast import PaperSearchFilters

page = await client.papers.search(
    PaperSearchFilters(
        year="2020-2023",
        fieldsOfStudy="Biology",
        openAccessPdf="true",
        minCitationCount=50,
    ),
    query="photosynthesis",
)
# the same keys work as a plain mapping
page = await client.papers.search({"venue": "Nature"}, query="crispr")
```

## Bulk search

```python
page = await client.papers.bulk_search("crispr", fields=["title", "year"], limit=1000)
page.next_cursor  # continuation token, None when done

# or let the client follow tokens
papers = [paper async for paper in client.papers.bulk_iterate("crispr", limit=5000)]
```

Bulk search returns up to 1000 records per call, ordered by corpus id
rather than relevance. It accepts the same filters as `search()`.

## Batch

```python
papers = await client.papers.batch(
    ["DOI:10.1038/nature12373", "ARXIV:1304.1068", "DOI:10.9999/nope"],
    fields=["title", "year"],
)
```

One `POST /paper/batch` call fetches up to 500 papers; the client chunks
longer lists. The API answers `null` for unknown ids and the client drops
those entries, so the result can be shorter than the id list. The POST is
a read and is sent with retries.

## Citations and references

```python
citations = await client.papers.citations(
    "DOI:10.1038/nature12373",
    fields=["title", "contexts", "intents", "isInfluential"],
    limit=100,
)
for citation in citations.results:
    citation.citingPaper.title
    citation.contexts  # text snippets where the citation appears
    citation.isInfluential

references = await client.papers.references(
    "DOI:10.1038/nature12373", fields=["title", "contexts"], limit=100
)
authors = await client.papers.authors("DOI:10.1038/nature12373")
```

Each call returns one page as a `Page`; `next_cursor` is the next offset
or `None` on the last page. The routes serve at most the most recent
10,000 edges per paper.

## Autocomplete and title match

```python
candidates = await client.papers.autocomplete("semanti")
# candidates[i].id, .title, .authorsYear

match = await client.papers.search_match(
    "Nanometer scale thermometry in a living cell", fields=["title", "year"]
)
match.paper  # the best-matching paper
match.matchScore
```

`search_match()` raises `NotFoundError` when no candidate passes the
relevance threshold.
