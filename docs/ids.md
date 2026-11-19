# Identifiers

`bibliofabric.ids` holds the canonical identifier normalizers shared by all
clients. They never URL-encode; clients add API-specific encoding on top.

| Function | Behavior |
|---|---|
| `normalize_doi` | Strips `https://doi.org/`, `dx.doi.org`, and `doi:` prefixes, trims, lowercases |
| `is_doi` | Whether the value looks like a bare DOI |
| `normalize_orcid` | Strips prefixes, returns the hyphenated 16-character form |
| `normalize_ror` | Strips prefixes, lowercases |
| `normalize_issn` | Returns the hyphenated uppercase form (`2049-3630`) |
| `strip_url_prefix` | Removes the first matching prefix, case-insensitively |

## API reference

::: bibliofabric.ids
    options:
      show_root_heading: true
