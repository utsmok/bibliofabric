# Activities

The activities summary (`GET /{orcid}/activities`) lists every section of the record. `client.activities.get(orcid)` validates it into `ActivitiesSummary`; a section the record does not use is `None`.

## Sections

Each section has a reader that hits the section route and returns its model, or `None` when the record has none of that kind.

| Method | Route | Element model |
|---|---|---|
| `works(orcid)` | `/{orcid}/works` | `WorkSummary` in `WorksSection` |
| `fundings(orcid)` | `/{orcid}/fundings` | `FundingSummary` |
| `educations(orcid)` | `/{orcid}/educations` | `EducationSummary` |
| `employments(orcid)` | `/{orcid}/employments` | `EmploymentSummary` |
| `peer_reviews(orcid)` | `/{orcid}/peer-reviews` | `PeerReviewSummary` |
| `distinctions(orcid)` | `/{orcid}/distinctions` | `DistinctionSummary` |
| `invited_positions(orcid)` | `/{orcid}/invited-positions` | `InvitedPositionSummary` |
| `memberships(orcid)` | `/{orcid}/memberships` | `MembershipSummary` |
| `qualifications(orcid)` | `/{orcid}/qualifications` | `QualificationSummary` |
| `research_resources(orcid)` | `/{orcid}/research-resources` | `ResearchResourceSummary` |
| `services(orcid)` | `/{orcid}/services` | `ServiceSummary` |

Works, fundings, and peer reviews group their summaries in `group` lists; the affiliation-style sections use `affiliation-group[].summaries[]`, where each summary is wrapped as `{"education-summary": {...}}` and so on. Every section model has a `put_codes()` helper that collects the put-codes you need for the single-item routes.

```python
works = await client.activities.works("0000-0002-1694-233X")
print(works.put_codes()[:5])
for group in works.group:
    for summary in group.work_summary:
        print(summary.put_code, summary.title.title.text, summary.type)
```

## Single items

Each put-code has a full route that returns the complete element, not the summary.

| Method | Route | Returns |
|---|---|---|
| `work(orcid, put_code)` | `/{orcid}/work/{put-code}` | `Work` |
| `works_bulk(orcid, put_codes)` | `/{orcid}/works/{code},{code},...` | `list[Work]`, up to 100 codes per request |
| `funding(orcid, put_code)` | `/{orcid}/funding/{put-code}` | `Funding` |
| `peer_review(orcid, put_code)` | `/{orcid}/peer-review/{put-code}` | `PeerReview` |
| `education(orcid, put_code)` | `/{orcid}/education/{put-code}` | parsed JSON object |
| `employment(orcid, put_code)` | `/{orcid}/employment/{put-code}` | parsed JSON object |
| `affiliation_item(orcid, kind, put_code)` | `/{orcid}/{kind}/{put-code}` | parsed JSON object |

`affiliation_item` covers `qualification`, `membership`, `service`, `distinction`, `invited-position`, and `research-resource`. These six share one shape with the affiliation summaries, so the client returns the parsed JSON object instead of one model per kind.

`works_bulk()` fetches many full works in one request per 100 put codes, which is the fastest way to read every work of a record: take the put codes from `works(orcid)` and pass them in. A put code that ORCID does not know answers an `error` entry and is absent from the result.

```python
work = await client.activities.work("0000-0002-1694-233X", 145464015)
print(work.title.title.text)  # Parsing and Matching Dates in VIAF
print(work.title.subtitle.text)  # Issue 26, 2014-10-21
print(work.journal_title.text)  # Code4Lib Journal
print(work.publication_date.iso())  # 2014-10-21
print(work.contributors.contributor[1].orcid.path)

funding = await client.activities.funding("0000-0002-1694-233X", 63665)
print(funding.organization.name)  # NSF Office of the Director
print(funding.organization.disambiguated_organization.identifier)
```

## Representations

`client.activities.representation(orcid, suffix, accept)` returns any route under the ORCID iD as text in another representation:

```python
xml = await client.activities.representation("0000-0002-1694-233X", "work/145464015")
```

## Bulk data

For a complete copy of the registry, ORCID publishes a public data file (a 17.4 GB tar.gz of XML for 2025) on `orcid.figshare.com`, documented under [Working with the Public Data File](https://info.orcid.org/documentation/integration-guide/working-with-bulk-data). This package does not download or parse it.
