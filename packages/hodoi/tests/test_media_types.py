"""The media type catalog and its consistency with the client."""

from hodoi import (
    AGENCY_SUPPORT,
    BIBTEX,
    CSL_JSON,
    DATACITE_JSON,
    JSON_MEDIA_TYPES,
    MEDIA_TYPES,
    RIS,
    SCHEMAORG_JSONLD,
    UNIXREF_XML,
)


def test_json_media_types_are_the_parsed_ones():
    assert JSON_MEDIA_TYPES == (CSL_JSON, DATACITE_JSON, SCHEMAORG_JSONLD)


def test_catalog_contains_the_documented_types():
    assert BIBTEX in MEDIA_TYPES
    assert RIS in MEDIA_TYPES
    assert UNIXREF_XML in MEDIA_TYPES
    assert len(MEDIA_TYPES) == len(set(MEDIA_TYPES))


def test_every_catalogued_type_lists_at_least_one_agency():
    for media_type, agencies in AGENCY_SUPPORT.items():
        assert media_type in MEDIA_TYPES
        assert agencies
