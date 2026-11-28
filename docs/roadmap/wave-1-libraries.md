# Wave 1 libraries

Wave 1 adds eleven single-source client libraries to the three existing ones. Each library covers every public read endpoint of its upstream API and models every field the API returns. Write endpoints are out of scope for this wave. The [deferred list](deferred.md) records what was left out and why.

Every library is built and tested under a placeholder name. The names are unique strings with no collision in the repository, so each one can be replaced with a single find-and-replace.

## Roster

Fill the real name into the last column.

| Library | Covers | Upstream docs | Placeholder | Real name |
|---|---|---|---|---|
| ROR | Organization records, search, filters, affiliation matching, registry dumps on Zenodo | [REST API](https://ror.readme.io/docs/rest-api) | `rorifer` | |
| Zenodo | Record search, record versions, files and downloads, communities, vocabularies, OAI-PMH harvesting | [REST API](https://developers.zenodo.org/) | `zenotheca` | |
| DataCite | DOIs, activities, clients, providers, repositories, prefixes, events, GraphQL queries | [REST API](https://datacite.readme.io/docs/datacite-rest-api-guide) | `dataphora` | |
| OpenCitations | Citation links, references, citation counts, and metadata | [API documentation](https://opencitations.github.io/) | `opcitato` | |
| DOI RA and content negotiation | Registration agency lookup, metadata by media type, handle records | [DOI resolution documentation](https://www.doi.org/the-identifier/resources/factsheets/doi-resolution-documentation) | `hodoi` | |
| Semantic Scholar | Papers, authors, citations, references, search, batch lookup, recommendations, patents, snippets, and dataset releases | [API docs](https://api.semanticscholar.org/api-docs/) | `scholiast` | |
| ORCID | Researcher records, person sections, activities, and both public search routes | [Public API guide](https://info.orcid.org/documentation/integration-guide/public-api/) | `orchis` | |
| Europe PMC | Literature search, article records, full text, references, citations, data links, evaluations, annotations, grants, profiles, and preprints | [Web services](https://europepmc.org/RestfulWebService) | `europaea` | |
| Wikidata | Entities, claims, sitelinks, lexemes, search, entity data in RDF formats, utility modules, and SPARQL | [Action API](https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities) | `quiddita` | |
| DOAJ | Journal and article search, journal and article records | [API v4 docs](https://doaj.org/api/v4/docs) | `diurnalia` | |
| ISSN Portal | ISSN and ISSN-L records as JSON-LD, the free search, and the Title Word Abbreviation list | [ISSN Portal](https://portal.issn.org/) | `seriatim` | |

## The placeholder names

Each placeholder has three spellings, and all three appear in code, tests, docs, and configuration. `uv.lock` carries a fourth, dashed form that `uv lock` writes.

| Spelling | Where it appears | Example |
|---|---|---|
| Lower case with underscore | Distribution name, import name, and the directories `packages/`, `src/`, and `docs/` | `rorifer` |
| Upper case with underscore | Prefix of the environment variables of the settings | `RORIFER_MAX_CONCURRENCY` |
| PascalCase without underscore | Prefix of the client, settings, and model class names | `RoriferClient` |
| Lower case with dash | The package entries of `uv.lock`, which `uv lock` rewrites | `dataphora` |

## Renaming a placeholder

Do this once the real name is registered on PyPI. For a real name `xyz`, the three spellings are `xyz`, `XYZ`, and `Xyz`.

1. Replace each placeholder spelling in the whole repository with a case-sensitive match. Start with the PascalCase spelling (`Rorifer`), then the upper case prefix (`RORIFER`), then the lower case name (`rorifer`), so that no replacement feeds the next one.
2. Rename the directories `packages/rorifer`, `packages/rorifer/src/rorifer`, and `docs/rorifer`.
3. Register the trusted publisher for `xyz` on PyPI. The publish job reads the package name from the tag `xyz-v<version>`, so the workflow needs no change.
4. From the repository root, run `uv lock`, then `uv run python scripts/unasync.py`, then the gates listed in the root `AGENTS.md`. The generator rewrites the `_sync/` directories from the renamed sources, and `uv lock` rewrites the lock entries, so neither needs a manual replacement.
5. Write the real name into the roster on this page.
6. Remove the placeholder notes that the rename leaves behind: the `tbd_*` paragraphs in the root `AGENTS.md`, `docs/contributing.md`, and `README.md`, and the naming sections on this page.

## Package pages

- [rorifer](../rorifer/index.md): [organizations](../rorifer/organizations.md), [data dumps](../rorifer/dumps.md), [upstream quirks](../rorifer/upstream-quirks.md), [API reference](../rorifer/reference.md)
- [zenotheca](../zenotheca/index.md): [records](../zenotheca/usage/records.md), [communities](../zenotheca/usage/communities.md), [vocabularies](../zenotheca/usage/vocabularies.md), [OAI-PMH](../zenotheca/usage/oai.md), [upstream quirks](../zenotheca/upstream-quirks.md), [API reference](../zenotheca/reference.md)
- [dataphora](../dataphora/index.md): [DOIs](../dataphora/usage/dois.md), [clients](../dataphora/usage/clients.md), [providers](../dataphora/usage/providers.md), [repositories](../dataphora/usage/repositories.md), [prefixes](../dataphora/usage/prefixes.md), [events](../dataphora/usage/events.md), [media and usage routes](../dataphora/usage/media.md), [GraphQL](../dataphora/usage/graphql.md), [upstream quirks](../dataphora/upstream-quirks.md), [API reference](../dataphora/reference.md)
- [opcitato](../opcitato/index.md): [Index API](../opcitato/index-api.md), [Meta API](../opcitato/meta-api.md), [upstream quirks](../opcitato/upstream-quirks.md), [API reference](../opcitato/reference.md)
- [hodoi](../hodoi/index.md): [registration agencies](../hodoi/agencies.md), [handle records](../hodoi/handles.md), [metadata by media type](../hodoi/metadata.md), [upstream quirks](../hodoi/upstream-quirks.md), [API reference](../hodoi/reference.md)
- [scholiast](../scholiast/index.md): [papers](../scholiast/papers.md), [authors](../scholiast/authors.md), [recommendations](../scholiast/recommendations.md), [datasets](../scholiast/datasets.md), [snippets and patents](../scholiast/other-routes.md), [upstream quirks](../scholiast/upstream-quirks.md), [API reference](../scholiast/reference.md)
- [orchis](../orchis/index.md): [records](../orchis/records.md), [person sections](../orchis/person.md), [activities](../orchis/activities.md), [search](../orchis/search.md), [upstream quirks](../orchis/upstream-quirks.md), [API reference](../orchis/reference.md)
- [europaea](../europaea/index.md): [search](../europaea/search.md), [articles](../europaea/articles.md), [annotations](../europaea/annotations.md), [grants, profiles, and preprints](../europaea/grants-profiles-preprints.md), [upstream quirks](../europaea/upstream-quirks.md), [API reference](../europaea/reference.md)
- [quiddita](../quiddita/index.md): [entities](../quiddita/entities.md), [search](../quiddita/search.md), [claims and statements](../quiddita/claims.md), [site links](../quiddita/sitelinks.md), [lexemes](../quiddita/lexemes.md), [SPARQL](../quiddita/sparql.md), [utility modules](../quiddita/utilities.md), [upstream quirks](../quiddita/upstream-quirks.md), [API reference](../quiddita/reference.md)
- [diurnalia](../diurnalia/index.md): [journals](../diurnalia/journals.md), [articles](../diurnalia/articles.md), [upstream quirks](../diurnalia/upstream-quirks.md), [API reference](../diurnalia/reference.md)
- [seriatim](../seriatim/index.md): [records](../seriatim/records.md), [search](../seriatim/search.md), [Title Word Abbreviations](../seriatim/ltwa.md), [upstream quirks](../seriatim/upstream-quirks.md), [API reference](../seriatim/reference.md)
