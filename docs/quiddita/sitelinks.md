# Site links

`client.sitelinks` reads the site links of an item through `wbgetentities`, without the rest of the entity.

```python
links = await client.sitelinks.get("Q42", sites=["enwiki", "dewiki"], with_urls=True)
print(links["enwiki"].title, links["enwiki"].url)
```

`get()` returns a `SitelinkMap` dict keyed by site id. `sites` maps to the `sitefilter` parameter; `with_urls=True` asks for the `sitelinks/urls` property so each `Sitelink` carries the resolved article URL.

The REST shape is available through `client.items.sitelink("Q42", "enwiki")`, which returns one `RestSitelink` from the `/entities/items/{id}/sitelinks/{site_id}` route.
