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

The argument can be a bare DOI or a DOI URL. Anything that is not a DOI name raises `ConfigurationError` before a request is sent. The client percent-encodes the DOI for the path, so a suffix with parentheses, angle brackets, colons, or a semicolon needs no extra work:

```python
sici = "10.1002/(SICI)1097-4636(199823)43:3<338::AID-JBM16>3.0.CO;2-B"
record = await client.handle(sici)
print(
    record.values[0].data.value
)  # https://onlinelibrary.wiley.com/doi/10.1002/(SICI)...
```

An unknown DOI answers HTTP 404 (`responseCode` 100), which raises `NotFoundError`. A record that exists but has no values answers `responseCode` 200 with an empty `values` list. A filter that matches no value answers the same way.

## Filters

```python
record = await client.handle("10.1038/nature12373", type="URL")
record = await client.handle("10.1038/nature12373", index=[1, 100])
record = await client.handle("10.1038/nature12373", type=["URL", "HS_ADMIN"])
record = await client.handle("10.1038/nature12373", auth=True, cert=True)
```

`type` and `index` restrict the returned values. Each takes one value or a list. A list is sent as repeated parameters, and the proxy returns the values that match any of them. A blank entry raises `ConfigurationError` before a request is sent.

`auth=True` bypasses the proxy cache and asks the primary handle server. The proxy caches values for up to 24 hours, so a freshly changed URL can be stale without it. `cert=True` asks the primary server for an authenticated answer.

## The record model

| Field | Content |
|---|---|
| `responseCode` | 1 success, 100 handle not found, 200 values not found |
| `handle` | The DOI as echoed by the proxy |
| `values` | List of `HandleValue` entries |
| `message` | Error explanation, on failures |

Each `HandleValue` has `index`, `type`, `data` (a `HandleValueData` with `format` and `value`), `ttl` in seconds, and an ISO 8601 `timestamp`. The `format` is `string` for the common text values, `admin` for `HS_ADMIN` (the value parses into a `HandleAdminValue`), and `base64`, `hex`, `vlist`, or `site` for the rarer shapes. Anything the client does not type passes through as extra fields.

## Landing URLs

```python
url = await client.landing_url("10.1038/nature12373")
# https://www.nature.com/articles/nature12373
```

`landing_url()` reads the `URL` entry of the record and returns it without fetching the landing page. It raises `ConfigurationError` when the record has no `URL` value.

## The redirect of a DOI

```python
response = await client.resolve("10.1038/nature12373")
print(response.status_code, response.headers["location"])
# 302 https://www.nature.com/articles/nature12373
```

`resolve()` sends `GET https://doi.org/{doi}` for `text/html` and returns the proxy's 302 as an `httpx.Response`. The `Location` header holds the landing page URL, and the body is a small HTML page titled "Handle Redirect". Redirects stay off unless the `HODOI_FOLLOW_REDIRECTS` setting is on, so the response is the 302 itself. An unknown DOI answers 404, which raises `NotFoundError`.

## The redirect targets of a DOI

```python
for location in await client.locations("10.1038/nature12373"):
    print(location.mode, location.http_role, location.href)
# legacy None https://www.nature.com/articles/nature12373
# None conneg https://api.crossref.org/v1/works/10.1038%2Fnature12373/transform
```

`locations()` sends `GET https://doi.org/{doi}?action=showurls`. The proxy answers an XML listing with one `location` element for every URL it could redirect to. An ordinary DOI has two entries. The landing page carries `mode="legacy"` and a numeric `weight`. The metadata server of the registration agency carries `http_role="conneg"` and a `href_template`, in which `{hdl}` stands for the DOI. A DOI with multiple resolution lists its further locations.

| Field | Content |
|---|---|
| `href` | The URL |
| `mode` | `legacy` for the landing page, otherwise `None` |
| `weight` | The proxy's preference as a string |
| `http_role` | `conneg` for the metadata server, otherwise `None` |
| `href_template` | The URL pattern of the metadata server |

Every other attribute of the element passes through as an extra field. An unknown DOI answers 404, which raises `NotFoundError`.
