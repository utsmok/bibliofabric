# Ecosystem Roadmap & Architecture

The `bibliofabric` monorepo is designed as a three-layer open scholarly
infrastructure stack:

```text
Layer 3: Canonical Entity Fusion (working name: bibliocanon)
         Multi-source PID resolution, per-field Claim provenance,
         license governance, SQLite/DuckDB cache, lossy exporters
                              ▲
Layer 2: Modular Single-Source Client Libraries
         Original: aireloom (OpenAIRE), aletheca (OpenAlex), stavrophora (Crossref)
         Wave 1 (built, not yet released): ROR v2, Zenodo, DataCite,
                  OpenCitations, DOI RA/ConNeg, Semantic Scholar, ORCID v3,
                  Europe PMC, Wikidata, DOAJ v4, ISSN Portal
         Wave 2:  Domain indexes, repositories, funder APIs, protocol adapters
                              ▲
Layer 1: bibliofabric Core Framework
         Async + generated sync HTTP, auth, retries, throttling, paging,
         batching, streaming, identifier normalizers, typed ResourceClient[E]
```

Each single-source library stays lean, typed, and faithful to its upstream API
schema. Cross-source entity deduplication, conflict resolution, and citation
export live strictly in the canonical fusion layer above them.

## 2025–2026 Academic API Ecosystem Shifts

API choices and build order reflect concrete platform changes across the
scholarly metadata ecosystem in 2025–2026:

- **OpenAlex credit tiers (2025–2026):** Moved to usage-based daily budgets. A
  free API key grants **$1.00/day** (resetting at midnight UTC and required for
  cursor paging past page 1), alongside prepaid credits and institutional tiers,
  exposing `X-RateLimit-Credits-Used` and `cost_usd`. Free/CC0 complementary
  sources (**DataCite, Europe PMC, OpenCitations, Semantic Scholar, ROR, DOAJ**)
  are increasingly valuable so pipelines avoid spending OpenAlex budget on
  metadata and crosswalks served elsewhere for free.
- **Crossref transitions (2026):**
  - The **Crossref Event Data** public API was **sunset on April 23, 2026**
    (historical dump archived on Academic Torrents), replaced by the
    **Crossref Data Citation API** (`/beta/datacitations/`, targeting GA late
    2026).
  - **Retraction Watch** data is now integrated into Crossref REST (`updated-by`
    / `update-type:retraction` with `source: retraction-watch`) alongside a
    daily GitLab CSV (`crossref/retraction-watch-data`).
  - Crossref's **Open Funder Registry** is formally transitioning into **ROR**
    (2024–2026); keep `/funders` for legacy `10.13039/...` → ROR crosswalks.
- **ROR v2:** API and schema **v1 were sunset in late 2025**. **ROR v2**
  (`api.ror.org/v2/organizations`, with v2.1 adding continents, domains,
  timestamps, and streamlined `single_search` affiliation matching) is required
  and now serves as the canonical registry for both organizations and funders.
- **Open Policy Finder (Jisc):** Replaced legacy **Sherpa RoMEO & Juliet**
  (`v2.sherpa.ac.uk` retired July 2026) at `api.openpolicyfinder.jisc.ac.uk`
  using `x-api-key` header authentication under **CC BY-NC-ND 4.0**.
  **OpenDOAR** migrated onto the same API and paused new submissions/updates
  pending review until January 2027.
- **OpenCitations consolidation:** Legacy `COCI`, `POCI`, and `/index/v1` are
  **deprecated/archived** in favor of unified **Index v2**
  (`api.opencitations.net/index/v2`) and **Meta v1**
  (`api.opencitations.net/meta/v1`).
- **Unpaywall (September 2026):** Retired `/v2/search` (`410 Gone`, redirecting
  callers to OpenAlex). Single-DOI lookup (`GET /v2/{doi}?email=...`) remains
  active (100k calls/day).
- **DOAJ v4:** API v1–v3 are deprecated; **API v4** (`doaj.org/api/v4`) is the
  active CC0 endpoint.
- **arXiv (October 2026):** Completed its cloud/database migration (arXiv-CE)
  and spun out as an independent nonprofit; Atom 1.0 XML and OAI-PMH remain the
  primary machine interfaces.

## Gaps in the Original Three Clients

`aireloom` (OpenAIRE), `aletheca` (OpenAlex), and `stavrophora` (Crossref)
already provide broad scholarly literature coverage, but leave five gaps. The
[Wave 1 libraries](wave-1-libraries.md) cover most of the first four gaps
with public read clients. The other sources named below stay Wave 2
candidates.

1. **Authority registries & PID crosswalks:** Canonical organization/funder
   hierarchies (**ROR v2**, **GLEIF LEI**), researcher-asserted profiles
   (**ORCID v3**), journal OA/APC/preservation metadata (**DOAJ v4**,
   **ISSN Portal / Keepers**, **Open Policy Finder**), universal PID bridging
   (**Wikidata**), and DOI Registration Agency routing (**`doi.org/ra`**).
2. **Research data & software:** Crossref is literature-centric and OpenAlex
   lacks file manifests, concept↔version DOIs, checksums, and intrinsic code
   identifiers. **DataCite**, **Zenodo (InvenioRDM)**, **Dryad**, **Dataverse**,
   **Figshare**, and **Software Heritage** fill this gap.
3. **Abstracts & full-text / bio-annotations:** Crossref lacks abstracts for
   many publishers and OpenAlex omits restricted abstracts. **Europe PMC**,
   **Semantic Scholar**, **PubMed**, and **CORE v3** provide rich abstracts,
   full-text links, and text-mined entities.
4. **Auditable citations & citation semantics:** **OpenCitations** provides 100%
   CC0 auditable citation links (OCIs) and OMID crosswalks; **Semantic Scholar**
   adds influential citations, TLDRs, citation intents, and SPECTER2 embeddings.
5. **Preprint versioning & research integrity:** **arXiv** and
   **bioRxiv/medRxiv** track preprint versions and preprint↔journal publication
   links; **Retraction Watch** + Crossref Crossmark provide safety-critical
   retraction coverage.

## Consolidated Build-Order Roadmap

### Phase 0 — Core Enablers & Existing-Client Extensions

1. **Six targeted `bibliofabric` core additions** (detailed in
   [Wave 1 Client Specs & Core Enablers](wave-1-clients.md#bibliofabric-core-enablers)):
   default per-client `Accept` headers, header-aware `ResponseUnwrapper` /
   RFC 5988 `Link` pagination, POST-body search dialect, sliding/fixed-window
   rate limiter + daily quota hooks, pluggable non-JSON (XML/SRU/Atom) decoder
   hook, and expanded `bibliofabric.ids` normalizers.
   Status on 2026-11-27: per-client headers and the JSON:API unwrapper are in
   `bibliofabric` 0.8, together with identifier normalizers for ISBN, ISNI,
   Wikidata, GND, and VIAF. The rest is listed in [Deferred work](deferred.md).
2. **Existing client enhancements:**
   - **`stavrophora` (Crossref):** Add the **Crossref Data Citation API**
     (`/beta/datacitations/`) and **Retraction Watch** (`updated-by` /
     `update-type:retraction`) helpers.
   - **`aletheca` (OpenAlex):** Expose OpenAlex credit/budget telemetry headers
     (`X-RateLimit-Credits-Used`, `cost_usd`) cleanly via `on_response()`.

   Status on 2026-11-28: all three are done. `stavrophora` has
   `client.data_citations` for the beta route and `Work.retractions` /
   `Work.is_retracted` for the Retraction Watch data, and the aletheca docs
   describe the credit and cost headers.

### Phase 1 — Wave 1: Authorities & Open Scholarly Graphs

Highest canonical ROI, open/free access, and permissive licensing (predominantly
CC0 / ODC-By / Public Domain):

- **Authorities & Routers:** ROR v2 (+ Zenodo dump loader & FundRef crosswalk),
  ORCID v3.0, DOAJ v4, DOI RA/ConNeg + ISSN Portal ConNeg, Wikidata (REST +
  `wbgetentities` batch).
- **Works, Citations, Data & Software:** DataCite REST (+ optional GraphQL),
  Semantic Scholar (Graph + Bulk + POST batch), OpenCitations (Index v2 + Meta
  v1), Europe PMC, Zenodo (reusable InvenioRDM pattern).

Status on 2026-11-28: all eleven libraries are built under their final names
and cover the public read endpoints of their APIs. See
[Wave 1 libraries](wave-1-libraries.md) for the roster and
[Deferred work](deferred.md) for what was left out.

### Phase 2 — Canonical Entity Fusion MVP

Build the fusion library (`bibliocanon`) above `bibliofabric` and the Wave 1
clients:

- Ten first-class canonical Pydantic models (`Work`, `Person`, `Organization`,
  `Venue`, `Publisher`, `Funder`, `Grant`, `Dataset`, `Software`, `Concept`).
- `Claim`-based per-field provenance, Union-Find PID equivalence clustering,
  declarative `FusionPolicy` with license gating (`commercial_safe=True`).
- Hybrid Waterfall + Scatter-Gather DAG planner with single-flight coalescing
  and per-source circuit breakers.
- SQLite OLTP + DuckDB OLAP local store, bulk snapshot loaders (ROR, DOAJ,
  Retraction Watch CSV, SPDX, CRediT), and lossy exporters (CSL-JSON, BibTeX,
  Schema.org JSON-LD, MLCommons Croissant, RIS, Parquet).

### Phase 3 — Wave 2: Specialists & Shared Protocol Adapters

- **Preprints, Data, Software & OA:** arXiv, bioRxiv/medRxiv, CORE API v3,
  Dryad v2, Harvard Dataverse (reusable across 100+ Dataverse instances),
  Figshare v2, Software Heritage, re3data, Unpaywall (lightweight lookup).
- **Domain Indexes & Registries:** DBLP, INSPIRE-HEP, NASA ADS / SciXplorer,
  HAL, ClinicalTrials.gov v2, PubMed / NCBI E-utilities, OSF Preprints,
  ChemRxiv, GLEIF LEI, Open Policy Finder (with `CC-BY-NC-ND` license guard),
  Open Library, Lobid-GND, VIAF, Mir@bel, HK-dir, JUFO, NIH RePORTER v2, NSF
  Award Search, UKRI GtR, RAiD, Identifiers.org, MeSH RDF.
- **Shared Protocol Adapters:** Generic **OAI-PMH** XML harvester mixin,
  **FAIR Signposting** `HEAD`/`Link` resolver, and **CodeMeta / `CITATION.cff`**
  software metadata parsers.

### Restricted, Commercial & Do-Not-Build List

Keep the open core free of legal/licensing blockers and deprecated endpoints:

- **Do not build (sunset/deprecated):** Crossref Event Data (sunset April 23,
  2026), ROR v1 (sunset late 2025), Sherpa v2 (`v2.sherpa.ac.uk`, retired July
  2026), OpenCitations `COCI`/`POCI`/`/index/v1`, Unpaywall `/v2/search`
  (retired September 2026), DOAJ v1–v3.
- **Do not scrape (closed/no public API):** ResearchGate, Loop (Frontiers),
  DFG GEPRIS (consume via OpenAIRE/Crossref), Ringgold Identify (resolve legacy
  IDs passively via Wikidata/ORCID/ISNI crosswalks).
- **Optional user-credentialed plugins only (proprietary / restricted ToS):**
  Lens.org, Dimensions, Scite, Altmetric, PlumX, PubPeer, OpenSyllabus,
  Elsevier Scopus/ScienceDirect, Springer Nature, IEEE Xplore, Wiley TDM, ACM
  DL, WorldCat v2, ISBNdb, OpenCorporates (ODbL + 50/day free cap), BASE
  (strictly non-commercial), OpenDOAR (CC BY-NC-ND + paused until Jan 2027),
  Google Books (non-redistributable caching ToS).
- **Periodic local tables (no live REST API):** Latindex, Scimago (SJR), CWTS
  Journal Indicators, MIAR.

## Roadmap Guides

- [Works, Citations, Preprints, Data & OA Catalog](api-landscape-works.md) —
  Structured catalog of scholarly work, citation, preprint, repository, data,
  software, integrity, and protocol APIs.
- [Authority Registries, Organizations, Venues, Funders & Taxonomies](api-landscape-registries.md) —
  Structured catalog of researcher, organization, venue, funder, PID, and
  controlled-vocabulary APIs.
- [Wave 1 Client Specs & Core Enablers](wave-1-clients.md) — Starter
  implementation specs for the 11 Wave 1 clients and the 6 `bibliofabric` core
  additions.
- [Wave 1 Libraries](wave-1-libraries.md) — The roster with the package
  names, their origins, and the release steps.
- [Deferred Work](deferred.md) — Everything Wave 1 left out, with the reason
  and the condition that unblocks it.
- [Canonical Entity Fusion Architecture](canonical-fusion.md) — End-to-end
  architecture blueprint for the canonical entity fusion library.
- [Building a client on `bibliofabric`](../bibliofabric/writing-a-client.md) —
  Practical guide to writing, testing, and shipping a new client package in this
  workspace.
