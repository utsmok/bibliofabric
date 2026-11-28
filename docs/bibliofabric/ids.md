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
| `normalize_isbn` | A valid ISBN-10 converts to its 978-prefixed ISBN-13 with a recomputed check digit; anything else comes back with hyphens and spaces removed and uppercased |
| `normalize_isni` | Four groups of four characters (`0000 0001 2109 7254`) |
| `normalize_arxiv` | Bare id; old-style ids lowercased; version suffix kept |
| `normalize_pmid` | Bare digits; strips `https://pubmed.ncbi.nlm.nih.gov/`, `pubmed:`, `pmid:` |
| `normalize_pmcid` | `PMC1234567`; bare digits get the `PMC` prefix |
| `normalize_wikidata_qid` | `Q42` or a property id such as `P3153`; strips `wikidata:`, `wd:`, wikidata.org URLs, and a `#fragment` |
| `normalize_gnd` | Bare id; a trailing `x` check digit becomes `X` |
| `normalize_viaf` | Bare cluster number without leading zeros |
| `strip_url_prefix` | Removes the first matching prefix, case-insensitively |

## API reference

::: bibliofabric.ids
    options:
      show_root_heading: true
