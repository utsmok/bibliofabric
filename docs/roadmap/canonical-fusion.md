# Canonical Entity Fusion Architecture

*(Working name: `bibliocanon` — an orchestration, entity-resolution, and fusion
library layered cleanly above `bibliofabric` and all single-source sibling
clients.)*

## Design Synthesis from Scholarly Knowledge Graphs

The architecture borrows proven patterns from major scholarly knowledge graphs
while keeping local-first Python SDK ergonomics (no Spark or RDF triplestore
required):

| System | Pattern Adopted | Pitfall Avoided |
|---|---|---|
| **OpenAIRE Graph** | Multi-stage deduplication (blocking → similarity → transitive closure) + explicit per-assertion provenance & trust scores (`0.0–1.0`). | Heavy batch Hadoop/Spark coupling; must run both on-demand (async single-entity) and in local batch pipelines. |
| **OpenAlex** | Flat, ergonomic canonical Pydantic models grounded in ROR, ORCID, ISSN-L, and DOI; CC0 openness. | Silent winner-takes-all overwrites where callers cannot inspect *which* source supplied a field or when. |
| **OpenCitations Meta (OMID)** | Internal stable IDs decoupled from external PIDs + versioned provenance snapshots. | Triplestore/Blazegraph operational overhead; implement the data model in Pydantic + SQLite/DuckDB instead. |
| **Wikidata / Scholia** | Claim-centric model `(value, qualifiers, source, confidence)` so conflicting claims coexist transparently. | Unbounded untyped schemas; preserve strict `ty`-checked Pydantic fields backed by a structured `claims` map. |
| **CERIF / Research Graph** | First-class temporal, role-typed relationships (`Person` —`[employed_at, 2020–2024]`→ `Organization`). | CERIF-XML verbosity; represent edges as typed Pydantic models with optional export adapters. |
| **CSL-JSON, BibTeX, Schema.org, Croissant** | Standard **lossy export projections** tailored to downstream tools. | Treating citation formats as the internal canonical schema (which drops affiliations, grants, OA policies, and provenance). |

## Layered Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    Canonical Entity Fusion Library                      │
│  ┌──────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│  │  EntityResolver  │→ │  EnrichmentPlanner  │→ │   FusionEngine     │  │
│  │ (PID norm + RA   │  │ (Waterfall / Scatter│  │ (Per-field policy, │  │
│  │  routing + graph)│  │  Gather + Budgets)  │  │  claims + license) │  │
│  └──────────────────┘  └─────────────────────┘  └─────────┬──────────┘  │
│                                                           ▼             │
│  ┌──────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│  │  SourceAdapters  │  │  LocalCache & Store │  │  ExportAdapters    │  │
│  │ (aireloom,       │  │ (SQLite / DuckDB    │  │ (CSL-JSON, BibTeX, │  │
│  │  stavrophora,    │  │  claims + ETag HTTP │  │  Schema.org, RIS,  │  │
│  │  aletheca, ror,  │  │  + local snapshots) │  │  Croissant,Parquet)│  │
│  │  orcid, doaj...) │  └─────────────────────┘  └────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│    bibliofabric core (Async/Sync HTTP, Auth, Limiter, Retries, IDs)     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Ten First-Class Canonical Entities

Every entity inherits from `CanonicalEntity`:

- `canonical_id: str` — deterministic internal URN (e.g.
  `urn:biblio:work:doi:10.1038/...`, or content-addressed hash
  `urn:biblio:work:sha256:...` when no hard PID exists).
- `identifiers: IdentifierSet` — normalized multi-PID registry
  (`dict[PidScheme, list[PidValue]]` with primary flag and source provenance).
- `same_as: list[str]` — external canonical URIs (`ror.org`, `orcid.org`,
  `wikidata.org`, `openalex.org`, `omid`).
- `claims: dict[str, list[Claim]]` — raw per-field assertions retained for
  auditability, offline re-fusion, and license filtering.
- `provenance: EntityProvenance` — per-source fetch timestamps, fusion policy
  version, source degradations, `has_conflict: bool`, and effective minimum
  SPDX license.

| Entity | Primary Hard PIDs (Anchors) | Secondary / Crosswalk PIDs | Key Canonical Attributes |
|---|---|---|---|
| **Work** *(articles, preprints, books, chapters, proceedings)* | `doi`, `isbn13`, `arxiv`, `pmid`, `pmcid`, `handle`, `ark` | `openalex`, `openaire`, `s2`, `omid`, `wikidata`, `hal`, `oclc`, `lccn` | Title, subtitle, type (COAR/CSL), pub dates, abstract, language, ordered authorships (+ CRediT + affiliations), venue ref, citations/references, OA status/URLs, SPDX license, retraction/correction status, funding links, subjects. |
| **Person / Author** | `orcid` | `isni`, `viaf`, `wikidata`, `gnd`, `lcnaf`, `idref`, `openalex`, `s2`, `scopus_author` | Canonical name + variants, bio, keywords, temporal employments/educations (ROR-linked), external profiles, disambiguated works. |
| **Organization** | `ror` | `lei`, `isni`, `wikidata`, `grid`, `fundref`, `ringgold`, `gnd`, `eter`, `deqar`, `openalex` | Canonical name + aliases/acronyms/translations, types, geo (country/city/coords/continent), domains, temporal parent/child/successor links, corporate ownership (LEI). |
| **Venue / Source** *(journals, series, conferences, repos)* | `issn_l`, `issn_p`, `issn_e` | `doaj`, `openalex`, `crossref_journal`, `jufo`, `kanalregister`, `mirabel`, `wikidata`, `isbn_prefix` | Key title + title history (predecessor/successor), venue type, publisher ref, OA model (Diamond/Gold/Hybrid/Closed), APC + currency, DOAJ Seal, Keepers preservation, Green OA policy, namespaced national ratings (HK-dir/JUFO). |
| **Publisher** | `ror`, `lei`, `crossref_member` | `doi_prefix[]`, `isbn_prefix[]`, `isni`, `wikidata`, `kanalregister`, `jufo` | Canonical name, corporate parent (LEI/ROR), owned DOI/ISBN prefixes, imprint hierarchy, default archiving policies. |
| **Funder** *(Organization role)* | `ror` *(2026 primary)* | `fundref` *(legacy `10.13039/...`)*, `wikidata`, `crossref_funder`, `openalex` | Organization core + funder type (gov/philanthropy/industry), country, OA mandate policy (Open Policy Finder), funded grants count. |
| **Grant / Project** | `raid`, `doi` (grant DOI), `(funder_ror, award_number)` | `cordis`, `nih_core_project`, `nsf_award`, `ukri_gtr`, `arc_grant`, `snsf`, `openaire_project` | Title, abstract, funder ref, award number, start/end dates, budget + currency, PIs (ORCID), administering/partner orgs (ROR), linked outputs. |
| **Dataset** | `doi`, `accession` (Identifiers.org CURIE), `ark` | `zenodo`, `dryad`, `figshare`, `openaire`, `openalex` | Work core + version chain (`isVersionOf`), files/distributions, checksums/format/size, SPDX license, funding, `isSupplementTo`, Croissant ML-structure fields. |
| **Software** | `doi`, `swhid`, `repo_url` | `ascl`, `rrid`, `openaire`, `wikidata` | Name, version/release, repository URL, languages, SPDX license, authors/maintainers (ORCID), `CITATION.cff`/CodeMeta metadata, linked papers. |
| **Concept / Subject** | Canonical URI (`mesh:`, `lcsh:`, `anzsrc:`, `unesco:`, `oecd_fos:`, `openalex_topic:`) | `wikidata`, `gnd`, `skos:exactMatch` / `closeMatch` | Preferred multilingual labels, altLabels, taxonomy scheme, broader/narrower hierarchy, tree code. |

## Identity Clustering & Guarded Links

Entity resolution maintains a bipartite equivalence graph
`(EntityCluster) ↔ (PidScheme, normalized_value)`:

1. **Hard 1:1 merges (Union-Find):** Normalized `doi`, `orcid`, `ror`,
   `issn_l`, `lei`, `raid`, `swhid`, `pmid`, and `wikidata` QID. Two records
   sharing any hard PID merge deterministically into one equivalence cluster.
2. **Guarded merges and version links (never collapsed destructively):**
   - **Print vs. Electronic ISSN:** Merge only through an authoritative
     **ISSN-L** from ISSN Portal or DOAJ, never blindly on title similarity.
   - **Preprint ↔ Version of Record (VoR):** An arXiv ID or bioRxiv DOI and its
     published journal DOI link via explicit `hasVersion` / `isVersionOf` edges
     rather than destructive merge, preserving distinct dates, licenses, and
     abstracts.
   - **ISBN-10 / ISBN-13:** Edition-level identifiers grouped under a parent
     Work cluster.
3. **Composite fallback keys:**
   - Grants lacking DOIs/RAiDs anchor on `(funder_ror, normalized_award_code)`.
   - Works lacking hard PIDs anchor on `(normalized_title_hash, year,
     first_author_surname)` with fuzzy verification (Jaro-Winkler / Levenshtein
     ≥ 0.92) before clustering.

## Per-Field Source Authority Matrix

| Entity | Field Group | Winning Authority Hierarchy (1st → Fallback) | Resolution Strategy |
|---|---|---|---|
| **Work** | Bibliographic core (title, dates, container, issue/pages, type) | **Crossref** (journal/book DOIs) / **DataCite** (datasets/software/preprints) → **DOI ConNeg** (JaLC/mEDRA) → **OpenAlex** → **OpenAIRE** → **Semantic Scholar** | `authority_priority` |
| **Work** | Abstracts | **PubMed / Europe PMC** → **Crossref** (JATS) → **OpenAIRE** → **Semantic Scholar** → **OpenAlex** | `authority_priority` |
| **Work** | Citations & References | **OpenCitations** ∪ **Crossref** ∪ **OpenAlex** ∪ **Semantic Scholar** ∪ **OpenAIRE** *(keep per-index counts separate)* | `union_with_dedup` |
| **Work** | OA Status, URLs & License | **Unpaywall / OpenAlex OA** ∪ **DOAJ** ∪ **Crossref** ∪ **OpenAIRE** *(normalized via **SPDX**)* | `union_with_dedup` + `authority_priority` |
| **Work** | Retractions, Corrections & EoCs | **Retraction Watch (Crossref)** → **Crossref Crossmark** → **PubMed** → **OpenAlex** | `safety_monotonic` (`any_true_with_evidence`) |
| **Work** | Funding links | **Crossref** ∪ **OpenAIRE** ∪ **NIH RePORTER / UKRI GtR** ∪ **OpenAlex** | `union_with_dedup` (tagged with confidence) |
| **Person** | Name, Bio, Temporal Affiliations, Curated Works | **ORCID** → **Wikidata** → **Lobid-GND / VIAF / IdRef / LCNAF** → **OpenAlex** → **Semantic Scholar** | `authority_priority` + `union_with_dedup` |
| **Organization** | Name, Hierarchy, Geo, Domains, Corporate Parent | **ROR v2** → **GLEIF LEI** *(legal form & parent corp)* → **Wikidata** → **DEQAR / ETER** → **OpenAlex** | `authority_priority` |
| **Venue / Journal** | ISSN-L, Key Title, Title History, Preservation | **ISSN Portal** *(ISSN-L & Keepers)* → **DOAJ** → **Crossref Journals** → **OpenAlex Sources** | `authority_priority` |
| **Venue / Journal** | OA Model, APC, Journal License, Peer Review | **DOAJ** → **Mir@bel** → **OpenAlex** | `authority_priority` |
| **Venue / Journal** | Green OA / Self-Archiving & Embargo Policies | **Open Policy Finder (Jisc)** *(tagged `CC-BY-NC-ND-4.0`)* → **Mir@bel** → **DOAJ** | `authority_priority` (license-gated) |
| **Venue / Journal** | National Quality Ratings / Book Publisher Tiers | **HK-dir (Kanalregisteret)**, **JUFO** *(stored as explicit namespaced ratings)* | `namespaced_map` |
| **Grant / Project** | Award Budget, Dates, PIs, Linked Outputs | **Native Funder API** *(NIH/NSF/UKRI/ARC/SNSF/CORDIS)* → **RAiD** → **OpenAIRE Projects** → **Crossref Grants** | `authority_priority` |
| **Dataset / Software** | Versions, Checksums, Files, License | **DataCite** / **Zenodo** / **Software Heritage** → **OpenAIRE** → **Crossref** → **OpenAlex** | `authority_priority` + `spdx_normalize` |

## `Claim` Provenance, Conflict Resolution & License Governance

Every ingested upstream field is recorded as an immutable `Claim`:

```python
Claim(
    field="title",
    value="...",
    source="crossref",
    source_record_id="10.1038/s41586-020-2649-2",
    retrieved_at=datetime(...),
    source_updated_at=datetime(...),
    confidence=1.0,
    license_spdx="CC0-1.0",
)
```

### Resolution Strategies (Declarative `FusionPolicy`)

1. **`authority_priority`:** Choose the claim from the highest-ranked source
   for that field (tie-breaking by `confidence`, then `source_updated_at`).
2. **`freshest_timestamp`:** Choose the latest `source_updated_at` for mutable
   operational metadata (APCs, OA URL liveness, current employment flags).
3. **`union_with_dedup`:** Merge normalized sets across sources (PIDs, aliases,
   OA locations, funding awards, references, subject terms), retaining the list
   of supporting sources per item. Never average incompatible citation counts
   across indexes; expose per-source counts side by side.
4. **`safety_monotonic` (`any_true_with_evidence`):** For retractions,
   expressions of concern, and errata, any verified authoritative positive claim
   surfaces prominently with evidence rather than being outvoted.
5. **`confidence_weighted`:** For inferred links (affiliation string → ROR,
   text-mined grants), accept claims at or above threshold (e.g. ROR
   `chosen=True` or OpenAIRE trust ≥ 0.8) and keep lower-confidence matches in
   `tentative_claims`.
6. **Raw claim retention & conflict surfacing:** Non-winning claims stay in
   `entity.claims[field]` and set `provenance.has_conflict = True` when
   high-tier sources materially disagree (e.g., publication year off by >1,
   conflicting retractions, mismatched ISSN-L).

### License Governance (`FusionPolicy`)

Because upstream licenses differ materially — **ROR, DOAJ, GLEIF, Wikidata,
Lobid-GND, OpenAlex, Crossref bibliographic facts, DataCite, OpenCitations, and
NIH/NSF** are CC0/Public Domain, while **Open Policy Finder** is
`CC-BY-NC-ND-4.0`, **ORCID Public API** carries non-commercial terms, and
**Google Books** restricts persistent redistribution — `FusionPolicy` enforces
licensing declaratively:

```python
policy = FusionPolicy(
    commercial_safe=True,
    allowed_licenses={"CC0-1.0", "CC-BY-4.0", "ODC-By-1.0", "OGL-UK-3.0"},
)
```

Disallowed sources are skipped during planning (saving quota) or stripped during
offline re-fusion and export, and every fused entity computes its effective
minimum license in `entity.provenance`.

## Hybrid Waterfall + Scatter-Gather Execution Engine

Pure scatter-gather wastes API quota (e.g. querying Crossref for a DataCite
DOI); pure sequential waterfall is too slow. The planner runs a **staged DAG**
with three built-in profiles (`fast`, `standard`, `deep`):

1. **Stage 0 — Local & Static Resolution (0 HTTP calls):** Normalize PIDs via
   `bibliofabric.ids`, query the local SQLite/DuckDB cache (with per-source
   TTLs, e.g. ROR/ISSN 30d, Work metadata 7d, Citations 1d), and consult static
   vocabularies (SPDX, CRediT, OECD FOS, ANZSRC) plus optional local ROR/DOAJ
   dumps (`<1 ms`).
2. **Stage 1 — Fast Anchor & Routing Call (1 call):**
   - For DOIs: check local prefix cache or call `doi.org/ra/{doi}` (batchable)
     to route straight to Crossref (`stavrophora`) vs. DataCite vs. ConNeg.
   - Fetch the primary anchor record (Crossref/DataCite for Work, ORCID for
     Person, ROR for Org, ISSN/DOAJ for Venue) to harvest secondary PIDs
     (`orcid`, `ror`, `issn`, `pmid`, `grant_id`).
3. **Stage 2 — Bounded Async Scatter-Gather (`run_bounded`):**
   - Fan out in parallel across complementary sources unlocked by Stage 1 PIDs.
   - Apply **single-flight request coalescing** so a batch of 50 works sharing
     1 journal ISSN or 3 ROR IDs fires only 1 upstream fetch per unique anchor.
4. **Stage 3 — Optional Recursive Graph Expansion (`depth=1..N`):** Hydrate
   linked `Author`, `Organization`, `Venue`, and `Grant` stubs into full
   canonical entities on demand.

### Partial Failure Tolerance

Every adapter runs inside a per-source timeout and isolated error boundary
(`on_error="degrade"` by default, `"raise"` optional) with a **per-source
circuit breaker** that opens after consecutive `5xx`/`429`/timeout failures so a
degraded registry (such as VIAF or LoC throttling) never stalls the pipeline.
Each resolution returns `FusionResult[E]`:

- `entity: E` — best canonical entity built from all succeeded sources
- `sources_succeeded: list[str]`
- `source_errors: dict[str, SourceFailure]` — typed status, retryable flag, and
  sanitized message
- `completeness: float` — fraction of target field groups populated

## Local Caching, Persistence & Bulk Snapshots

Persistence is organized into three tiers:

- **Tier 1 — Raw HTTP ETag/TTL Cache (SQLite):** Stores
  `(source, canonical_request_key) → (etag, last_modified, status, gzip_json,
  fetched_at, ttl)` to enable `If-None-Match` conditional revalidation for
  slow-changing authorities (ROR, Wikidata, MeSH, SPDX).
- **Tier 2 — Claim & Entity Graph Store (SQLite OLTP + DuckDB OLAP):**
  - `entities(canonical_id, entity_type, payload_json, updated_at, schema_version)`
  - `identifiers(scheme, value, canonical_id, primary_flag, source)` — indexed
    for O(1) PID crosswalk and Union-Find cluster lookups.
  - `claims(canonical_id, field, value_json, source, source_record_id,
    confidence, license_spdx, retrieved_at)` — retaining raw claims allows
    callers to **re-run `FusionEngine` offline** under a different
    `FusionPolicy` (e.g. toggling `commercial_safe=True` or changing source
    priority) without re-querying any API.
  - `relations(src_id, rel_type, dst_id, qualifiers_json, source, confidence)` —
    CERIF-style typed temporal edges.
  - **DuckDB bridge:** Zero-copy SQL analytics and Parquet export over millions
    of fused entities and claims.
- **Tier 3 — Local Bulk Snapshot Loaders:** First-class loaders for compact,
  high-value open dumps — **ROR Zenodo dump (~115k orgs)**, **DOAJ journal dump
  (~21k journals)**, **Retraction Watch daily GitLab CSV (~50k+ rows)**, plus
  static **SPDX**, **CRediT**, and **ANZSRC** tables — turning the highest-hit
  lookups into `<1 ms` zero-network calls.

## Lossy Export Adapters

All exporters live under `exports/` with zero network I/O and optional
license-compliance validation before serialization:

| Exporter | Output Format | Primary Target |
|---|---|---|
| `to_csl_json(work)` | CSL-JSON | Pandoc, Zotero, Citeproc (`id`, `type`, `DOI`, `ISSN`, `ISBN`, `author`, `issued.date-parts`, `container-title`) |
| `to_bibtex(work)` | BibTeX / BibLaTeX | LaTeX workflows (deterministic citekeys, LaTeX escaping, `@article`/`@inproceedings`/`@book`/`@software`/`@dataset`) |
| `to_schema_org(entity)` | Schema.org JSON-LD | Web/SEO & knowledge graphs (`ScholarlyArticle`, `Person`, `Organization`, `Periodical`, `Grant`, `SoftwareSourceCode`, `Dataset` with `@id` & `sameAs`) |
| `to_croissant(dataset)` | MLCommons Croissant JSON-LD | ML-ready dataset metadata (`schema.org/Dataset` + `cr:distribution`, `cr:recordSet`, `cr:field`) |
| `to_ris(work)` | RIS | Legacy reference managers & systematic review tools (EndNote, RefWorks, Rayyan, Covidence) |
| `to_parquet(entities)` | Apache Parquet / Arrow | Columnar bibliometrics & ML pipelines (flattened entities, PID crosswalks, and edge tables via PyArrow/DuckDB) |
