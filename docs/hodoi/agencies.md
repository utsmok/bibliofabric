# Registration agencies

Every DOI is registered with exactly one registration agency (RA). The proxy answers `GET /ra/{doi}` with a JSON list that names it. `client.agencies()` sends that request and returns `AgencyAnswer` models.

## One DOI

```python
answer = await client.agency("10.1038/nature12373")
print(answer.DOI, answer.RA)  # 10.1038/nature12373 Crossref
```

The argument can be a bare DOI, a `https://doi.org/` URL, or a `doi:` string; the client strips the wrapper before sending. Anything that is not a DOI after that raises `ConfigurationError`.

## Many DOIs

```python
answers = await client.agencies(
    ["10.1038/nature12373", "10.5281/zenodo.1238808", "10.1400/56174"]
)
print([(answer.DOI, answer.RA) for answer in answers])
# Crossref, DataCite, mEDRA
```

`agencies()` joins the DOIs with commas into one request, in chunks of 100 (`hodoi.RA_BATCH_SIZE`). A longer URL would fail: the proxy answered HTTP 414 (URI Too Long) for a 500-DOI request. The result order follows the request order across chunks.

## Unknown and malformed DOIs

The proxy answers HTTP 200 in every case. A known DOI carries `RA`; an unknown or malformed one carries a `status` string instead:

| Input | Answer |
|---|---|
| Known DOI | `RA` is the agency name (`Crossref`, `DataCite`, `mEDRA`, ...) |
| Unregistered DOI | `status` is `DOI does not exist` |
| Malformed string | `status` is `Invalid DOI` |
| Unknown prefix | `status` is `Unknown` |

`AgencyAnswer` models both shapes: `RA` is `None` when `status` is set. Nothing raises; decide from `answer.RA` or `answer.status`.

## Model

| Field | Content |
|---|---|
| `DOI` | The DOI as echoed by the proxy |
| `RA` | The agency name, or `None` for a status answer |
| `status` | The error string, or `None` for a known DOI |

Unknown extra fields pass through (`extra="allow"`).
