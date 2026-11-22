# Links

`client.links` talks to the `/links` endpoint and returns `Link` models: typed one-hop edges between works, each labeled with a link-type URL (`https://openalex.org/link-types/citation` and the part-of link types). OpenAlex renamed these from "relationships" on 2026-11-14; models accept the old field name until the 2026-12-07 cutover and map old `/relationships/` ids to `/link-types/`.

```python
references = await client.links.origin("W2741809807")  # edges leaving the work
citations = await client.links.target("W2741809807")  # edges pointing at it
reviews = await client.links.target("W2741809807", link_type="review")  # one kind only
```

`origin()` sends `filter=origin:<id>` and `target()` sends `filter=target:<id>`; both cursor-page up to `limit` (default 100) edges and take `link_type=` to keep one kind (`citation`, `volume`, `component`, `data-series`, `part`, or `review`; full link-type URLs shorten to the value form). Bare `W...` ids and full URLs normalize. Each `Link` exposes `origin`, `target`, and `link_type`. A list request costs one credit.

Use `client.links.search({"origin": "W..."})` or `iterate()` for raw queries beyond the two helpers.
