# API reference

Generated from the source with mkdocstrings.

## Client

::: quiddita.QuidditaClient
    options:
      heading_level: 3
      show_source: false
      members:
        - entities
        - search
        - claims
        - sitelinks
        - items
        - properties
        - statements
        - sparql
        - request

## Sync client

::: quiddita.QuidditaSyncClient
    options:
      heading_level: 3
      show_source: false
      members:
        - entities
        - search
        - claims
        - sitelinks
        - items
        - properties
        - statements
        - sparql
        - request

## Settings

::: quiddita.QuidditaSettings
    options:
      heading_level: 3
      show_source: false

## Resource clients

The `entities` and `search` resources inherit the generic operations from `bibliofabric.ResourceClient` (`get`, `search`, `iterate`, `collect`, `first`, `count`) through `quiddita._async.base.WikidataResourceClient`. Only the members that Wikidata changes or adds are shown here.

::: quiddita._async.entities.EntitiesClient
    options:
      heading_level: 3
      show_source: false
      members:
        - get
        - iterate_ids
        - _fetch_batch_chunk

::: quiddita._async.search.SearchClient
    options:
      heading_level: 3
      show_source: false
      members:
        - search
        - count
        - search_items
        - search_properties
        - suggest_items
        - suggest_properties

::: quiddita._async.claims.ClaimsClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.sitelinks.SitelinksClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.rest_items.ItemsClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.rest_items.PropertiesClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.statements.StatementsClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.entity_data.EntityDataClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.lexemes.LexemesClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.utilities.UtilitiesClient
    options:
      heading_level: 3
      show_source: false

::: quiddita._async.sparql.SparqlClient
    options:
      heading_level: 3
      show_source: false

## Helpers and dialect

::: quiddita.normalize_wikidata_id
    options:
      heading_level: 3
      show_source: false

::: quiddita.dialect
    options:
      heading_level: 3
      show_source: false
      members:
        - ACTION_API_BASE_URL
        - ACTION_PATH
        - MAX_IDS_PER_REQUEST
        - MAX_SEARCH_LIMIT
        - REST_PREFIX
        - SPARQL_BASE_URL
        - SPARQL_PATH
        - WIKIDATA_DIALECT

::: quiddita.unwrapper.QuidditaUnwrapper
    options:
      heading_level: 3
      show_source: false

## Models

The models live in `quiddita.models` and are re-exported from the top-level package. They are plain Pydantic models with `extra="allow"`.

::: quiddita.models.Entity
    options:
      heading_level: 3
      show_source: false
      members:
        - label
        - description

::: quiddita.models.Term
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.Claim
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.Snak
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.DataValue
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.Reference
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.Sitelink
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.EntitySearchResult
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestItem
    options:
      heading_level: 3
      show_source: false
      members:
        - label
        - description

::: quiddita.models.RestProperty
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestStatement
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestQualifier
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestReference
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestSitelink
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestSearchResult
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.SparqlResult
    options:
      heading_level: 3
      show_source: false
      members:
        - rows

::: quiddita.models.SparqlBindingValue
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.EntityDataResult
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.EntityDataDocument
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.RestLexeme
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.ParsedValue
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.PropertySuggestion
    options:
      heading_level: 3
      show_source: false

::: quiddita.models.CheckedClaim
    options:
      heading_level: 3
      show_source: false
