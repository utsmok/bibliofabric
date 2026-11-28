# SPARQL

`client.sparql` talks to the SPARQL query service at `https://query.wikidata.org/sparql`. The service is a second host, so it runs on its own client instance behind the resource.

## Running queries

```python
result = await client.sparql.query(
    "SELECT ?item ?label WHERE { ?item wdt:P31 wd:Q5 } LIMIT 5"
)
print(result.head.vars)
for row in result.rows():  # plain {variable: value} strings
    print(row["item"])
```

`query()` sends `GET` with `format=json` and returns a typed `SparqlResult` (the SPARQL 1.1 JSON result: `head.vars` and `results.bindings` with typed `SparqlBindingValue` terms carrying `type`, `value`, `xml_lang`, and `datatype`).

Long queries belong in a POST body, where URL length limits do not apply:

```python
result = await client.sparql.query_post(long_query)
```

`query_post()` sends a read-only POST and therefore passes `retry=True` so the framework retries transient failures.

## Other formats

`query_text()` passes the raw body through as text. The representation is selected through the `Accept` header (the service ignores a non-JSON `format` query parameter): `json`, `xml`, `csv`, `tsv`, or `turtle`.

```python
csv_body = await client.sparql.query_text(query, format="csv")
```

## Two hosts, one pace

`QuidditaClient` owns one rate limiter built from `QuidditaSettings`. `client.sparql` builds a `QuidditaQueryClient` for `query.wikidata.org` that receives the same settings object and the main client's limiter instance. Requests are paced by rate class inside that shared limiter: Action API and REST requests use the `default` class (2 requests per second by default), SPARQL requests use the `sparql` class (one query every 2 seconds by default), and one concurrency bound covers both hosts. The result: the two clients together never exceed the pace the settings describe, and no separate coordination is needed.

## Errors

Malformed or overlong queries answer with HTTP 400 and a plain-text Java stack trace; the framework raises `APIError` with that text attached as the body. The service cancels queries that run longer than its timeout.
