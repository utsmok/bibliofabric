# Annotations

`client.annotations` talks to the annotations API at
`https://www.ebi.ac.uk/europepmc/annotations_api`, a separate service from
the REST web services. Every method sends `format=JSON`.

## Annotations of articles

```python
records = await client.annotations.by_article_ids(
    ["MED:23903748", "PMC:PMC4221854"], type="Chemicals"
)
for record in records:
    for annotation in record.annotations:
        print(annotation.exact, annotation.tags[0].name)
```

`by_article_ids` takes one article id or a list (comma-joined into the
`articleIds` parameter) and returns one `ArticleAnnotations` record per
article. Optional filters: `type` (annotation type such as `Chemicals`,
`Diseases`, `Taxonomy`), `sub_type`, `section` (a JATS section such as
`Methods`), and `provider`.

## Annotations of entities, providers, and relationships

The other routes page with cursor marks (a float) and return
`AnnotationPage` models; `next_cursor_mark` is `None` once the API reports
exhaustion.

```python
page = await client.annotations.by_entity("aspirin", page_size=100)
while page.next_cursor_mark is not None:
    for record in page.articles:
        ...
    page = await client.annotations.by_entity(
        "aspirin", cursor=page.next_cursor_mark, page_size=100
    )

await client.annotations.by_provider("Europe PMC", page_size=100)
await client.annotations.by_relationship("aspirin", "heart", page_size=100)
await client.annotations.by_section(type="Diseases", page_size=100)
```

`by_provider` takes a provider name such as `Europe PMC`, `OpenTargets`, or
`HES-SO_SIB`; an unknown name answers 400. `by_section` covers the whole
annotation store without a filter, so it requires at least `type` or
`section` and raises `ConfigurationError` otherwise.
