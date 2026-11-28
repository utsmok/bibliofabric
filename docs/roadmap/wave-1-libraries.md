# Wave 1 libraries

Wave 1 adds eleven single-source client libraries to the three existing ones. Each library covers every public read endpoint of its upstream API and models every field the API returns. Write endpoints are out of scope for this wave. The [deferred list](deferred.md) records what was left out and why.

The libraries are not yet published on PyPI. The [release section](#release) lists what each first release needs.

## Roster

| Library | Package | Covers | Upstream docs |
|---|---|---|---|
| ROR | `rorifer` | Organization records, search, filters, affiliation matching, registry dumps on Zenodo | [REST API](https://ror.readme.io/docs/rest-api) |
| Zenodo | `zenotheca` | Record search, record versions, files and downloads, communities, vocabularies, OAI-PMH harvesting | [REST API](https://developers.zenodo.org/) |
| DataCite | `dataphora` | DOIs, activities, clients, providers, repositories, prefixes, events, GraphQL queries | [REST API](https://datacite.readme.io/docs/datacite-rest-api-guide) |
| OpenCitations | `opcitato` | Citation links, references, citation counts, and metadata | [API documentation](https://opencitations.github.io/) |
| DOI RA and content negotiation | `hodoi` | Registration agency lookup, metadata by media type, handle records | [DOI resolution documentation](https://www.doi.org/the-identifier/resources/factsheets/doi-resolution-documentation) |
| Semantic Scholar | `scholiast` | Papers, authors, citations, references, search, batch lookup, recommendations, patents, snippets, and dataset releases | [API docs](https://api.semanticscholar.org/api-docs/) |
| ORCID | `orchis` | Researcher records, person sections, activities, and both public search routes | [Public API guide](https://info.orcid.org/documentation/integration-guide/public-api/) |
| Europe PMC | `europaea` | Literature search, article records, full text, references, citations, data links, evaluations, annotations, grants, profiles, and preprints | [Web services](https://europepmc.org/RestfulWebService) |
| Wikidata | `quiddita` | Entities, claims, sitelinks, lexemes, search, entity data in RDF formats, utility modules, and SPARQL | [Action API](https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities) |
| DOAJ | `diurnalia` | Journal and article search, journal and article records | [API v4 docs](https://doaj.org/api/v4/docs) |
| ISSN Portal | `seriatim` | ISSN and ISSN-L records as JSON-LD, the free search, and the Title Word Abbreviation list | [ISSN Portal](https://portal.issn.org/) |

## Names

The names follow the existing family. `aireloom` weaves OpenAIRE, `aletheca` is a library of truth for OpenAlex, and `stavrophora` is Greek for "cross bearer", after Crossref. Each Wave 1 name is a Latin or Greek word that points at its source.

| Package | Origin |
|---|---|
| `rorifer` | Latin for "dew bearing" (*ros*, *roris*), and it starts with ROR. |
| `zenotheca` | Zeno plus *theca* (library). Zenodo is named after Zenodotus, the first librarian of Alexandria. |
| `dataphora` | "Data bearer", the DataCite counterpart of `stavrophora`. |
| `opcitato` | From *opere citato* ("in the work cited"), the "op. cit." of footnotes. |
| `hodoi` | Greek for "roads" or "ways". The client routes a DOI to its registration agency, and the word contains "doi". |
| `scholiast` | A scholar who writes scholia, the notes in the margins of a text. |
| `orchis` | The Greek and botanical name of the orchid, after ORCID. |
| `europaea` | Latin for "European", after Europe PMC. |
| `quiddita` | From *quidditas* ("whatness"), for the Q identifiers of Wikidata. |
| `diurnalia` | Latin for daily records, the root of "journal", after the Directory of Open Access Journals. |
| `seriatim` | Latin for "one after another", for serials and their ISSNs. |

Each name has three spellings: the distribution and import name (`rorifer`), the prefix of the settings environment variables (`RORIFER_MAX_CONCURRENCY`), and the prefix of the class names (`RoriferClient`).

## Release

1. Register a pending trusted publisher on PyPI for each name: owner `utsmok`, repository `bibliofabric`, workflow `ci.yml`, environment `pypi`. The publish job reads the package name from the tag `<name>-v<version>`, so the workflow needs no change.
2. Release `bibliofabric` 0.8.0 first, because every Wave 1 library requires `bibliofabric>=0.8,<0.9`. Release `aireloom`, `aletheca`, and `stavrophora` next with their new pins.
3. Tag each Wave 1 library as `<name>-v0.1.0`, following the release flow in the root `AGENTS.md`.

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
