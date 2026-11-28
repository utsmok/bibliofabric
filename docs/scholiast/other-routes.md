# Other routes

Snippets and patents live on the graph base URL alongside papers and
authors.

## Snippets

`client.snippets.search()` talks to `/snippet/search`. Snippets are
excerpts of roughly 500 words drawn from a paper's title, abstract, and
body text. The route needs an API key with snippet access.

```python
result = await client.snippets.search("protein folding", fields=["text"], limit=10)
result.retrievalVersion
for match in result.data:
    match.score
    match.snippet.text
    match.snippet.snippetKind  # bodyText, title, abstract, ...
    match.snippet.annotations.sentences
    match.snippet.annotations.refMentions  # with matchedPaperCorpusId
    match.paper.title  # minimal paper record
    match.paper.openAccessInfo
```

The default limit is 10 and the API maximum is 1000.

## Patents

`client.patents` talks to the `/patent` routes.

```python
patent = await client.patents.get("US10296086B2", fields=["title", "abstract"])
patent.ucid
patent.title

page = await client.patents.search("neural network", fields=["title"], limit=100)
page.results  # Patent records
page.next_cursor  # next offset as a string

citations = await client.patents.outbound_citations(
    "CorpusId:4314121", fields=["title"], limit=100
)
citations.citingPaperInfo  # the cited paper
citations.data  # the citing patents
```

`get()` answered keyless on 2026-11-27 with a minimal record (`title`,
`ucid`). `search()` and `outbound_citations()` are in the published API
spec; the study could not observe their keyless behavior because the
shared pool answered 429 in that window. The `Patent` model declares the
documented fields (`applicationUcids`, `cpcCodes`, `claims`,
`citedUcids`, `filingDate`, `publicationDate`, and more) and keeps
unknown fields in `model_extra`.
