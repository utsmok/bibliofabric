# orchis package notes

## Layout

`src/orchis/_async/` is the single source of truth. `scripts/unasync.py`
generates `src/orchis/_sync/` and `tests/_sync/`; never hand-edit those.
Pure modules (config, dialect, models, unwrapper) live at the package root.

Resource clients live in `_async/resources.py`. All routes are bound to an
ORCID iD, so every client overrides `item_path()` to produce
`/{orcid}/{suffix}` and `normalize_id()` to accept URLs and compact ids via
`bibliofabric.ids.normalize_orcid`. `ORCID_ITEM_DIALECT` disables paging for
record-bound routes; `ORCID_SEARCH_DIALECT` maps `rows` to page size and
`start` to a zero-based offset.

## Upstream facts (verified 2026-11-27, about 48 paced requests)

- The record, person, and activities routes answer JSON with
  `Accept: application/json` (also with `application/vnd.orcid+json`) and
  XML with `application/xml` or no `Accept` header. `application/ld+json`
  answers 406 on the public API.
- `/{orcid}/biography` and `/{orcid}/emails` answer 404 (error code 9041)
  when the record has none. Empty lists such as keywords and peer-reviews
  answer 200 with an empty list. An unused section such as distinctions
  answered 404 in one run and 200 with an empty group in another; the
  section readers therefore turn any 404 into `None`.
- Single-item routes use the singular segment (`/{orcid}/work/1234`); the
  plural segment (`/{orcid}/works/1234`) answers the same body.
- `/expanded-search/` answers `{"expanded-result": [...], "num-found": N}`;
  `start` past the total answers `{"expanded-result": null, "num-found": N}`.
  `rows=1000` and an unknown field such as `bogus-field:x` answer HTTP 500
  with a Solr exception in `developer-message`.
- `/search/` answers `{"result": [{"orcid-identifier": ...}], "num-found": N}`.
- ORCID documents 12 requests per second for anonymous and public API
  callers and 24 for the member API, with a burst of 40 and a 503 above the
  burst. Daily quotas are 25,000 reads per IP anonymously and 100,000 per
  client id for the public API. The client defaults to 4 requests per second.
- The credentials in the repo `.env` are public API credentials: the member
  API answers 403 on `https://api.orcid.org/v3.0/{orcid}/record`, so it is
  not wrapped. `ORCHIS_CLIENT_ID` and `ORCHIS_CLIENT_SECRET` mint a
  `/read-public` token through `ClientCredentialsAuth` (form-post client
  authentication); `ORCHIS_ACCESS_TOKEN` takes precedence. Test settings
  pass `access_token=None, client_id=None, client_secret=None`.
- The public data file is documented at
  `https://info.orcid.org/documentation/integration-guide/working-with-bulk-data`
  and hosted on `orcid.figshare.com`; the 2025 file is a 17.4 GB tar.gz of
  XML. This package does not cover it.

## Testing

Offline tests run without `PYTHONPATH` extras beyond the standard command in
the root AGENTS.md; live tests live in `tests/_async/test_live_api.py` under
`pytestmark = pytest.mark.live_api` and fetch the same record the fixtures
were trimmed from (`0000-0002-1694-233X`). Live runs must stay paced; the
client itself throttles to the settings rate.
