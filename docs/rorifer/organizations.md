# Organizations

`client.organizations` talks to `/organizations` and returns `Organization` models. Pages hold 20 records, and the API serves pages 1 to 500, so one query reaches at most 10,000 records. A query with more results raises `ConfigurationError` when page 501 would be needed. To read the whole registry, use a [data dump](dumps.md).

## Get one record

```python
org = await client.organizations.get("006hf6230")
org = await client.organizations.get("https://ror.org/006hf6230")  # same record
org = await client.organizations.get("ror.org/006hf6230")  # same record
found = await client.organizations.exists("006hf6230")
```

The bare ROR id, the record URL, and the form `ror.org/006hf6230` work. `get()` returns records of every status, including inactive and withdrawn ones, and raises `NotFoundError` for an id that does not exist. `exists()` returns `False` for a missing record. It sends `GET`, because the ROR gateway answers `HEAD` with 403.

## The record model

| Field | Content |
|---|---|
| `id` | The record URL, such as `https://ror.org/006hf6230` |
| `names` | `Name` entries with `value`, `lang` (which may be `None`), and `types` (`ror_display`, `label`, `alias`, `acronym`) |
| `display_name` | The `ror_display` name, else the first `label`, else the first name |
| `types` | Any of `archive`, `company`, `education`, `facility`, `funder`, `government`, `healthcare`, `nonprofit`, `other` |
| `status` | `active`, `inactive`, or `withdrawn` |
| `established` | The year as an integer |
| `domains` | Website domains |
| `links` | `Link` entries of type `website` or `wikipedia`, with the URL in `value` |
| `locations` | `Location` entries with `geonames_id` and `geonames_details` (continent, country, subdivision, `lat`, `lng`, `name`) |
| `external_ids` | `ExternalId` entries with `type` (`grid`, `isni`, `wikidata`, `fundref`), `all`, and `preferred` |
| `relationships` | `Relationship` entries with `type` (`parent`, `child`, `related`, `successor`, `predecessor`), the other record's `id`, and a `label` |
| `admin` | `created` and `last_modified`, each with `date` and `schema_version` |

`external_ids_of_type("fundref")` returns every id of one scheme. Fields that ROR adds later are kept in `model_extra`.

## Search

```python
page = await client.organizations.search(query="university of twente")
page.total  # 132 on 2026-11-27
page.results  # up to 20 Organization records
page.meta  # facet counts: types, countries, continents, statuses
```

`query` is a keyword search over names and external ids. It finds a FundRef id (`query=100000001`) and a Wikidata id (`query=Q1547084`, in upper case), but it does not find an ISNI.

`advanced` takes an Elasticsearch query string for the `query.advanced` parameter, for example `names.value:"University of Twente"` or `established:[1900 TO 2000]`. ROR rejects a request that carries both `query` and `advanced`; the client raises `ConfigurationError` with ROR's message.

Only active records answer by default. Pass `all_status=True` to include inactive and withdrawn records.

```python
page = await client.organizations.search(
    {"types": ["education", "nonprofit"], "country.country_code": "NL"},
    advanced="established:[1900 TO 2000]",
    all_status=True,
    page=2,
)
```

ROR has no sort, field selection, cursor, or page-size parameters. Passing `sort=`, `select=`, `cursor=`, or `page_size=` raises `ConfigurationError` without a request.

## Filters

Filters travel in one `filter` parameter as `key:value` pairs. A list value repeats its key, which means OR, and different keys are joined with commas, which means AND. Pass a plain dict or the `OrganizationFilters` model. The model accepts the dot notation of the API (`country.country_code`) and the Python attribute name (`country_country_code`).

| Key | Matches |
|---|---|
| `status` | `active`, `inactive`, or `withdrawn` |
| `types` | One or more of the nine organization types |
| `country.country_code` | ISO 3166-1 alpha-2 code, such as `NL` |
| `country.country_name` | Country name in the spelling of ROR |
| `locations.geonames_details.country_code` | Country code of one location |
| `locations.geonames_details.country_name` | Country name of one location |
| `locations.geonames_details.continent_code` | Continent code, such as `eu` |
| `locations.geonames_details.continent_name` | Continent name, such as `Europe` |

Any other key is a rejected request. The filter models allow extra fields, so a key that ROR adds later still works. Prefer the codes over the names, because a name must match the spelling of ROR exactly.

## Iterate and count

```python
async for org in client.organizations.iterate(
    {"types": "education", "country.country_code": "NL"}, limit=1_000
):
    print(org.id)

total = await client.organizations.count(query="university of twente")
```

`iterate()` fetches page after page and stops at `limit`, at an empty page, or when `number_of_results` records were seen. A query with more than 10,000 results raises `ConfigurationError` at page 501; it does not stop with the first 10,000 records. `count()` returns `number_of_results`; ROR has no count-only route, so it fetches one page. `collect()` and `first()` accept the same arguments as `iterate()`.

ROR warns that a paged query without a filter can repeat or skip records between pages. For a complete list, narrow the query with a filter or read a [data dump](dumps.md).

## Affiliation matching

```python
matches = await client.organizations.match_affiliation("Dept of Physics, MIT")
chosen = next(match.organization for match in matches if match.chosen)
```

ROR returns up to 10 `AffiliationMatch` candidates. Each carries the matched `substring`, a `score` from 0 to 1, a `matching_type`, and `chosen`, which is true for exactly one candidate. The full record is in `organization`.

## Identifier lookup and the funder crosswalk

```python
from rorifer import fundref_id_from_doi

# By any external id, in any spelling the client knows
await client.organizations.find_by_external_id("0000000403998953", id_type="isni")

# By a Crossref Funder Registry DOI
nsf = await client.organizations.find_by_funder_doi("10.13039/100000001")
fundref_id_from_doi("10.13039/100000001")  # "100000001"
```

`find_by_external_id()` searches the stored spelling exactly, so it tries every spelling ROR may keep. An ISNI is searched in its grouped and its compact form, and a Wikidata id in lower and upper case. `id_type` restricts the result to one scheme (`fundref`, `grid`, `isni`, `wikidata`). The lookup includes inactive and withdrawn records. ROR cannot search a value that contains a double quote, a backslash, or a colon, so pass the bare id; anything else raises `ConfigurationError`.

`find_by_funder_doi()` runs the same lookup for a Crossref Funder Registry DOI. `fundref_id_from_doi()` and `fundref_doi_from_id()` convert between the DOI and the FundRef id.
