# Registration agencies

Every DOI is registered with exactly one registration agency (RA). The proxy answers `GET /ra/{doi}` with a JSON list that names it. `client.agencies()` sends that request and returns `AgencyAnswer` models.

## One DOI

```python
answer = await client.agency("10.1038/nature12373")
print(answer.DOI, answer.RA)  # 10.1038/nature12373 Crossref
```

The argument can be a bare DOI, a `https://doi.org/` URL, or a `doi:` string. The client strips the wrapper and sends the rest. It does not reject a malformed string, because the proxy answers a malformed string with `status: "Invalid DOI"` instead of an error. A query string or fragment in the URL is cut first, as in `https://doi.org/10.1038/nature12373?from=mail`.

## Many DOIs

```python
answers = await client.agencies(
    ["10.1038/nature12373", "10.5281/zenodo.1238808", "10.1400/56174"]
)
print([(answer.DOI, answer.RA) for answer in answers])
# Crossref, DataCite, mEDRA
```

`agencies()` joins the DOIs with commas into one request. A request holds at most 100 DOIs (`hodoi.RA_BATCH_SIZE`) and stays under 4000 path characters (`hodoi.RA_MAX_PATH_CHARS`), so a list of long DOIs takes more, smaller requests. The result order follows the request order across requests.

A longer URL would fail. The proxy answered HTTP 414 (URI Too Long) for a 500-DOI request.

## Unknown and malformed DOIs

The proxy answers HTTP 200 in every case. A known DOI carries `RA`; an unknown or malformed one carries a `status` string instead:

| Input | Answer |
|---|---|
| Known DOI | `RA` is the agency name (`Crossref`, `DataCite`, `mEDRA`, ...) |
| Unregistered DOI | `status` is `DOI does not exist` |
| Malformed string | `status` is `Invalid DOI` |
| Unknown prefix | `status` is `Unknown` |

`AgencyAnswer` models both shapes. `RA` is `None` when `status` is set. Nothing raises for an unknown or malformed DOI. Decide from `answer.RA` or `answer.status`.

Two inputs raise before a request is sent. An empty list raises `ConfigurationError`, and so does a blank DOI.

## Encoding in the path

The client percent-encodes every DOI before it enters the path, because the proxy decodes the path before it matches the DOI. `10.1000/a#b` travels as `/ra/10.1000/a%23b`. A comma inside a DOI travels as `%2C`, so it does not split the list.

## Model

| Field | Content |
|---|---|
| `DOI` | The DOI as echoed by the proxy |
| `RA` | The agency name, or `None` for a status answer |
| `status` | The error string, or `None` for a known DOI |

Unknown extra fields pass through (`extra="allow"`). Every entry of the answer is validated. A body that is not a list raises `ConfigurationError`, and an entry that is not an object raises `ValidationError`.
