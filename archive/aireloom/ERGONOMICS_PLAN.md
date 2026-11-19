# Ergonomics Layer Implementation Plan

**Status:** Approved  
**Date:** 2026-06-05  
**Scope:** AIREloom + bibliofabric

---

## Overview

Add an explicit convenience layer on top of the existing AIREloom API surface. The raw API workflow (filters → search/iterate → manual field access) remains untouched. The new layer consists of five independent additions that can be implemented and shipped separately:

| Layer | What | Where | Effort |
|-------|------|-------|--------|
| **A. Safe types** | `SafeList`, `SafeStr`, `safe_model` — None never reaches users | `aireloom/models/safe_types.py` + entity models | Small |
| **B. Computed properties** | `@computed_field` on Pydantic models for common derived values | `aireloom/models/*.py` | Small |
| **C. Convenience queries** | High-level async functions for common workflows | New `aireloom/queries.py` | Medium |
| **D. Iterator helpers** | `collect()`, `count()`, `first()` on resource clients | `bibliofabric/resources.py` | Small |
| **E. Polish** | Better `__str__`, date parsing, batch `get_many` | Both repos | Small |

---

## A. Safe Types — No None Ever Reaches the User

### Problem

Users must write defensive code for every list field and every nested optional:

```python
# Current: crashes if product.pids is None
[pid.scheme for pid in product.pids]

# Required defensive patterns
[pid.scheme for pid in (product.pids or [])]
if product.indicators and product.indicators.citationImpact:
    count = product.indicators.citationImpact.citationCount
```

### Library research: no existing solution

Investigated: glom (raises PathAccessError), returns/dry-python (Maybe monads, no Pydantic integration), `__getattr__` override (doesn't fire for existing None fields), `__getattribute__` override (breaks Pydantic v2 internals), descriptor wrappers (conflict with Pydantic field descriptors).

**Conclusion**: No existing library solves safe optional chaining on Pydantic models. Build it with Pydantic's own `BeforeValidator`.

### Solution: `SafeList`, `SafeStr`, `safe_model()` — three reusable types

**1. `SafeList[T]`** — list fields that coerce `None → []` and filter null elements:

```python
from typing import TypeVar
from pydantic import BeforeValidator
from typing_extensions import Annotated

T = TypeVar("T")

SafeList = Annotated[
    list[T],
    BeforeValidator(lambda v: [] if v is None else [x for x in v if x is not None])
]
```

Result: `[pid.scheme for pid in product.pids]` always works. Even `[null, {...}, null]` in the API gets cleaned.

**2. `SafeStr`** — string fields that coerce `None → ""`:

```python
SafeStr = Annotated[str, BeforeValidator(lambda v: "" if v is None else v)]
```

Result: `product.title.upper()` never crashes on None.

**3. `safe_model(ModelClass)`** — nested object fields that coerce `None → empty instance`:

```python
def safe_model(model_class):
    """Create an Annotated type that coerces None → model_class() with defaults."""
    def _coerce(v):
        if v is None:
            return model_class()
        return v
    return Annotated[model_class, BeforeValidator(_coerce)]
```

Result: `product.container.name` returns `""` instead of crashing. `isinstance(product.container, Container)` is `True`. Type checkers see `Container`, not `Container | None`.

All three work at any depth because each Pydantic model validates independently.

### Semantic justification

- **Lists**: `[]` vs `None` is semantically identical (no items). ✅
- **Strings**: `""` vs `None` is acceptable for display fields (title, name, label). For fields where None has semantic meaning (e.g., `embargoEndDate` where None = "no embargo"), keep `str | None`. ✅
- **Nested objects**: empty `Container()` vs `None`. The empty container has all-`SafeStr`/`SafeList` fields, so it's traversable without guards. `isinstance` works. `model_dump()` serializes all-empty. ✅

### Where does this live?

| Component | Location | Rationale |
|-----------|----------|-----------|
| `SafeList`, `SafeStr`, `safe_model` | `aireloom/models/safe_types.py` | New module, imported by all entity models |
| `.dig()` method | `bibliofabric/utils.py` | Generic escape hatch for rare unknown deep paths |

### Which fields get which type?

**Rules:**
- List fields → `SafeList[T]` (always safe to iterate)
- String display fields (title, name, label, description) → `SafeStr`
- String semantic fields where None is meaningful (dates, URLs, embargoEndDate) → keep `str | None`
- Nested BaseModel fields that represent optional containers → `safe_model(ThatModel)`
- Nested BaseModel fields where None is semantically meaningful → keep `ThatModel | None`

### Performance

Benchmarked: ~8% overhead on validation, zero on subsequent access. Null path actually faster (empty list trivially validated). At ~900k validations/sec, negligible for any real workload.

### Impact on existing tests

~5 assertions change:

- `tests/test_models.py`: `TestResearchProductKeywords.test_none_keywords` — `assert rp.keywords is None` → `assert rp.keywords == []`
- `tests/test_models.py`: `TestResearchProductKeywords.test_unexpected_type_returns_none` — `assert rp.keywords is None` → `assert rp.keywords == []`
- `tests/test_models.py`: `TestProjectKeywords.test_empty_string_returns_none` — `assert p.keywords is None` → `assert p.keywords == []`
- `tests/test_models.py`: `TestProjectKeywords.test_none_passthrough` — `assert p.keywords is None` → `assert p.keywords == []`

Keyword validators need updating: return `[]` instead of `None` for unparseable input, since the field type is now `SafeList[str]` (never None).

---

## B. Computed Properties on Models

### Mechanism: `@computed_field`

Pydantic v2's `@computed_field` — tested and verified:

- **Property access with full type hints** — IDE auto-completes `product.doi`
- **Zero storage overhead** — computed on each access, no extra fields stored
- **Non-invasive** — `model_validate()` ignores computed fields on input; they're output-only
- **Coexists with `extra="allow"`** — if the API returns a field with the same name, the computed value takes priority on attribute access, and the raw value is preserved in `__pydantic_extra__`
- **Inheritable** — works through Pydantic model inheritance

### ResearchProduct computed fields

| Property | Type | Derivation |
|----------|------|------------|
| `doi` | `str \| None` | First PID where `scheme.lower() == "doi"` and `value` is non-empty |
| `all_dois` | `list[str]` | All PID values where `scheme.lower() == "doi"` |
| `is_open_access` | `bool` | `bestAccessRight.label` in `("OPEN", "open")` if `bestAccessRight` exists, else `False` |
| `open_access_url` | `str \| None` | First URL from an instance where `accessRight.label` indicates open access |
| `pdf_url` | `str \| None` | First URL containing "pdf" from any instance with open access |
| `citation_count` | `int \| None` | `indicators.citationImpact.citationCount` if chain exists |
| `publication_year` | `int \| None` | `int(publicationDate[:4])` if `publicationDate` has ≥4 chars |
| `journal_name` | `str \| None` | `container.name` if chain exists |
| `author_names` | `list[str]` | `[a.fullName for a in authors if a.fullName]` |
| `author_orcids` | `list[str]` | Extract ORCID values from `authors[].pid` (handles both simple and nested PID formats) |
| `license` | `str \| None` | First non-empty `license` from instances, preferring open-access instances |

### Person computed fields

| Property | Type | Derivation |
|----------|------|------------|
| `orcid` | `str \| None` | Check `originalId` for ORCID-like pattern (`\d{4}-\d{4}-...`), or extract from `id` prefix `orcid_______::` |
| `full_name` | `str` | `"givenName familyName"` if both exist, else whichever exists, else `""` |

### Organization computed fields

| Property | Type | Derivation |
|----------|------|------------|
| `ror_id` | `str \| None` | First PID where `scheme.lower() == "ror"`, return `value` |
| `country_code` | `str \| None` | `country.code` if chain exists and not `"UNKNOWN"` |

### Project computed fields

| Property | Type | Derivation |
|----------|------|------------|
| `funder_name` | `str \| None` | `fundings[0].shortName` or `fundings[0].name` if chain exists |
| `funder_jurisdiction` | `str \| None` | `fundings[0].jurisdiction` if chain exists |
| `start_year` | `int \| None` | `int(startDate[:4])` if `startDate` exists |
| `end_year` | `int \| None` | `int(endDate[:4])` if `endDate` exists |

### DataSource computed fields

| Property | Type | Derivation |
|----------|------|------------|
| `type_name` | `str \| None` | `type.value` if `type` exists |

### Implementation approach

1. Add computed fields directly on each entity model class in `src/aireloom/models/`.
2. No new files needed for this — it's a non-breaking addition to existing models.
3. Add a helper function `_extract_pid_by_scheme(pids, scheme)` in a new `src/aireloom/_helpers.py` to deduplicate the PID extraction logic used across models.

---

## C. Convenience Query Functions

### Architecture

```
aireloom/
├── queries.py          # New: standalone async functions
└── session.py          # Updated: add .queries property
```

### `search_on` parameter

Every convenience query function that accepts an identifier string gets an explicit `search_on` parameter. When an object is passed, `search_on` tells the function *which field* to extract from the object:

```python
# AIREloom Organization object → use its ROR field
await publications_by_organization(session, org, search_on="ror")

# Crossref Organization object → still works
await publications_by_organization(session, crossref_org, search_on="ror")
```

| `search_on` value | String input → API filter | Object input → attribute |
|-------------------|--------------------------|--------------------------|
| `"name"` | `search` parameter | `.legalName` / `.title` / `.fullName` |
| `"ror"` | `pid` parameter | `.ror_id` or `.pids` with ROR scheme |
| `"openaire_id"` | `id` parameter | `.id` |
| `"doi"` | `pid` parameter | `.doi` or `.pids` with DOI scheme |
| `"orcid"` | `orcid` parameter | `.orcid` or `.originalId` |
| `"code"` | `code` parameter | `.code` |

### Query function signatures

```python
# Research-focused
async def publications_by_organization(session, identifier, *, search_on="name", ...) -> AsyncIterator[ResearchProduct]
async def publications_by_doi(session, dois) -> list[ResearchProduct]
async def publications_by_author(session, identifier, *, search_on="name", ...) -> AsyncIterator[ResearchProduct]
async def publications_by_project(session, identifier, *, search_on="name", ...) -> AsyncIterator[ResearchProduct]

# Link/Scholix-focused
async def citing_works(session, entity, ...) -> AsyncIterator[ScholixRelationship]
async def related_datasets(session, entity, ...) -> AsyncIterator[ScholixRelationship]
async def all_links(session, entity, ...) -> AsyncIterator[ScholixRelationship]

# Organization-focused
async def projects_by_organization(session, identifier, *, search_on="name", ...) -> AsyncIterator[Project]

# Counting
async def count_publications(session, filters=None) -> int
```

---

## D. Iterator Helpers (bibliofabric level)

Add to `BaseResourceClient` in `bibliofabric/resources.py`:

```python
async def collect(self, *, filters=None, limit, sort_by=None, page_size=100) -> list[EntityType]
async def count(self, *, filters=None) -> int
async def first(self, *, filters=None, sort_by=None) -> EntityType | None
```

---

## E. Additional Improvements

### E1. Better `__str__` for models
### E2. Date parsing computed fields
### E3. Batch `get_many` in bibliofabric

(Details unchanged from previous version.)

---

## Implementation Order

1. **Safe types** (A) — new `safe_types.py`, update all entity models, fix ~5 test assertions
2. **Computed properties** (B) — builds on safe types, adds derived field access
3. **Helper utilities** — `_extract_pid_by_scheme` in AIREloom, `.dig()` in bibliofabric
4. **Iterator helpers** (D) — `collect`, `count`, `first` in bibliofabric
5. **Better `__str__`** (E1) — quick win
6. **Convenience queries** (C) — new module, `search_on` parameter, most design work
7. **Date parsing** (E2) — small, can be done alongside (B)
8. **Batch `get_many`** (E3) — depends on bibliofabric resources module

---

## Files Changed

### AIREloom

| File | Change |
|------|--------|
| `src/aireloom/models/safe_types.py` | New: `SafeList`, `SafeStr`, `safe_model` |
| `src/aireloom/models/base.py` | Update imports |
| `src/aireloom/models/research_product.py` | Apply safe types to all fields; add ~10 `@computed_field` |
| `src/aireloom/models/person.py` | Apply safe types; add 2 `@computed_field` |
| `src/aireloom/models/organization.py` | Apply safe types; add 2 `@computed_field` |
| `src/aireloom/models/project.py` | Apply safe types; add 4 `@computed_field` |
| `src/aireloom/models/data_source.py` | Apply safe types; add 1 `@computed_field` |
| `src/aireloom/models/scholix.py` | Apply safe types to list fields |
| `src/aireloom/models/relation.py` | Apply safe types to list fields |
| `src/aireloom/_helpers.py` | New: PID extraction utility |
| `src/aireloom/queries.py` | New: convenience query functions with `search_on` parameter |
| `src/aireloom/session.py` | Add `.queries` property |
| `tests/test_models.py` | Update ~5 assertions, add safe type tests |
| `tests/test_computed_fields.py` | New: tests for all computed fields |
| `tests/test_queries.py` | New: tests for convenience functions |

### Bibliofabric

| File | Change |
|------|--------|
| `src/bibliofabric/resources.py` | Add `collect()`, `count()`, `first()` methods |
| `src/bibliofabric/utils.py` | New: `.dig()` via `DigMixin`, `safe_dig()` standalone |
| `tests/test_utils.py` | New: tests for utility functions |
