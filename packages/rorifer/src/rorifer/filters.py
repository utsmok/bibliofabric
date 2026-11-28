"""Pydantic filter models for the ROR API.

Each field maps to one key of the ``filter=key:value`` parameter of the
organizations route. The keys are the eight ROR documents (verified
2026-11-27); any other key comes back as a rejected request. Every model
allows extra fields, so filters added upstream stay usable before they land
here.
"""

from collections.abc import Sequence

from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_isni, normalize_wikidata_qid
from pydantic import BaseModel, ConfigDict, Field

_StrFilter = str | Sequence[str] | None
_SharedConfig = ConfigDict(extra="allow", populate_by_name=True)


class OrganizationFilters(BaseModel):
    """Filter model for the ``/organizations`` route.

    A sequence value ORs its items (``types=["education", "nonprofit"]``) and
    different keys AND. ``status`` is ``active``, ``inactive``, or
    ``withdrawn``. Country codes are ISO 3166-1 alpha-2 in any case; country
    and continent names must match ROR's spelling exactly (``The
    Netherlands``), so prefer the codes.
    """

    model_config = _SharedConfig

    status: _StrFilter = None
    types: _StrFilter = None
    country_country_code: _StrFilter = Field(None, alias="country.country_code")
    country_country_name: _StrFilter = Field(None, alias="country.country_name")
    locations_country_code: _StrFilter = Field(
        None, alias="locations.geonames_details.country_code"
    )
    locations_country_name: _StrFilter = Field(
        None, alias="locations.geonames_details.country_name"
    )
    locations_continent_code: _StrFilter = Field(
        None, alias="locations.geonames_details.continent_code"
    )
    locations_continent_name: _StrFilter = Field(
        None, alias="locations.geonames_details.continent_name"
    )


def external_id_query(value: str, *, id_type: str | None = None) -> str:
    """Return the ``query.advanced`` clause that matches one external id.

    ROR compares ``external_ids.all`` with the stored spelling and case, so
    the clause ORs every spelling ROR may store: the value as given, an ISNI
    in its grouped and its compact form, and a Wikidata id in upper case.
    ROR's query parser cannot search a value that contains ``"``, ``\\`` or
    ``:``, so those raise :class:`ConfigurationError`; pass the bare id.
    """
    wanted = value.strip()
    if not wanted:
        raise ConfigurationError("value must be a non-empty external id.")
    if any(char in wanted for char in '"\\:'):
        raise ConfigurationError(
            "ROR cannot search an external id that contains '\"', '\\' or ':', "
            f"got {value!r}. Pass the bare id as ROR stores it."
        )
    candidates = [wanted]
    if id_type in (None, "isni"):
        grouped = normalize_isni(wanted)
        candidates += [grouped, grouped.replace(" ", "")]
    if id_type in (None, "wikidata"):
        candidates.append(normalize_wikidata_qid(wanted))
    phrases = dict.fromkeys(f'external_ids.all:"{item}"' for item in candidates)
    return " OR ".join(phrases)


__all__ = ["OrganizationFilters", "external_id_query"]
