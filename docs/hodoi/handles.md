# Handles

A DOI is a Handle System identifier. The proxy exposes the underlying record at `GET /api/handles/{doi}`, and `client.handle()` types it as `HandleRecord`.

## Read a record

```python
record = await client.handle("10.1038/nature12373")
print(record.responseCode)  # 1
for value in record.values:
    print(value.index, value.type, value.data.format)
# 1 URL string
# 700050 700050 string
# 100 HS_ADMIN admin
```

An unknown DOI answers HTTP 404 (`responseCode` 100), which raises `NotFoundError`. A record that exists but has no values answers `responseCode` 200 with an empty `values` list.

## Filters

```python
record = await client.handle("10.1038/nature12373", type="URL")
record = await client.handle("10.1038/nature12373", index=1)
record = await client.handle("10.1038/nature12373", auth=True)
```

`type` and `index` restrict the returned values. `auth=True` bypasses the proxy cache and asks the primary handle server; the proxy caches values for up to 24 hours, so a freshly changed URL can be stale without it.

## The record model

| Field | Content |
|---|---|
| `responseCode` | 1 success, 100 handle not found, 200 values not found |
| `handle` | The DOI as echoed by the proxy |
| `values` | List of `HandleValue` entries |
| `message` | Error explanation, on failures |

Each `HandleValue` has `index`, `type`, `data` (a `HandleValueData` with `format` and `value`), `ttl` in seconds, and an ISO 8601 `timestamp`. The `format` is `string` for the common text values, `admin` for `HS_ADMIN` (the value parses into a `HandleAdminValue`), and `base64`, `hex`, `vlist`, or `site` for the rarer shapes; anything the client does not type passes through as extra fields.

## Landing URLs

```python
url = await client.landing_url("10.1038/nature12373")
# https://www.nature.com/articles/nature12373
```

`landing_url()` reads the `URL` entry of the record and returns it without fetching the landing page. It raises `ConfigurationError` when the record has no `URL` value. To actually fetch the page, pass the URL to your HTTP library of choice, or call `client.content(doi, "text/html")`-style requests through `raw()`.
