# AIREloom Improvement Plan

**Date:** 2026-06-05
**Source:** Cross-library comparison with syntheca (OpenAlex client, `~/dev/aletheca/`)

These findings were identified during a thorough comparison of both libraries' structure, architecture, and completeness. Only aireloom-specific improvements are listed here.

---

## 1. [High] Add `py.typed` PEP 561 Marker

Syntheca has `src/syntheca/py.typed` (empty file). Both libraries claim `Typing :: Typed` in their PyPI classifiers, but aireloom is missing the marker file that signals PEP 561 typing support to downstream type checkers.

**Action:** Create `src/aireloom/py.typed` (empty file).

---

## 2. [High] Move `verification_script.py` to `scripts/`

Syntheca organizes verification scripts under `scripts/verify.py`. Aireloom's `verification_script.py` sits at the repo root, cluttering the top-level directory alongside source code, docs, and config.

**Action:**
```bash
mkdir -p scripts
git mv verification_script.py scripts/verification_script.py
```
Update any references to the script path.

---

## 3. [Medium] Add `.python-version` File

Syntheca has `.python-version` pinning the Python interpreter version. Aireloom doesn't, relying on `pyproject.toml`'s `requires-python` alone. Adding it improves `uv` and `pyenv` auto-detection.

**Action:** Create `.python-version` with content `3.12` (or whatever the target version is).

---

## 4. [Medium] Remove Committed `.ruff_cache/` Directory

The `.ruff_cache/` directory is committed to git (visible in directory listing with subdirectories like `0.15.16/`, `0.11.12/`). This is a build artifact that should be gitignored.

**Action:**
```bash
# Add to .gitignore
echo '.ruff_cache/' >> .gitignore
# Remove from git tracking
git rm -r --cached .ruff_cache/
git commit -m "chore: gitignore .ruff_cache"
```

---

## 5. [Low] Consider Typed ID Models

Syntheca has dedicated `src/syntheca/models/ids.py` with typed ID models per entity:
- `WorkIds`, `AuthorIds`, `SourceIds`, `InstitutionIds`, etc.
- Each with typed fields (e.g., `doi: SafeStr | None`, `openalex: SafeStr | None`)

Aireloom uses `list[str]` or `dict` for PIDs and identifiers. Adding typed models would improve:
- IDE autocomplete
- Runtime validation
- Documentation clarity

**Consider for:** `Pid` model already exists but could be expanded with typed accessor methods or additional structured fields.

---

## Potential Bibliofabric Improvements (Cross-Cutting)

### Shared `SafeTypes` Module

Both libraries implement identical `SafeList` and `SafeStr` Pydantic validators independently:
- `src/aireloom/models/safe_types.py` (79 lines)
- `src/syntheca/models/safe_types.py` (20 lines)

The logic is the same: coerce `None` → empty list/string, strip `None` from list elements. Moving to `bibliofabric.safe_types` as a shared module would eliminate duplication and ensure consistent behavior.

### Generalize Filter Serialization

Syntheca overrides `_serialize_filters()` in a base resource client to produce OpenAlex's `filter=key:value,key:value` format. This pattern could be generalized in bibliofabric as a pluggable serialization strategy, reducing consumer boilerplate.

### Document Iterator Helpers in Base Framework

`collect()`, `count()`, `first()` are provided by bibliofabric mixins but documented only in each consumer's docs. Adding framework-level docs would reduce duplication.
