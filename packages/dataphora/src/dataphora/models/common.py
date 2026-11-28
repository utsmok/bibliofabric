"""Shared model machinery for DataCite JSON:API resources.

Every DataCite resource travels as a JSON:API resource object with ``id``,
``type``, ``attributes``, ``relationships``, and ``links`` keys. The models
here flatten that envelope so each model exposes ``id``, every attribute
field, and the ``relationships`` and ``links`` objects at the top level. All
models allow extra fields, so attributes DataCite adds stay available as
``model_extra`` after parsing.
"""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class DataphoraModel(BaseModel):
    """Base for all DataCite models: extra attributes are kept, not dropped."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class JsonApiIdentifier(DataphoraModel):
    """A resource linkage entry (``{"id": ..., "type": ...}``)."""

    id: str | None = None
    type: str | None = None
    lxid: str | None = None


class JsonApiRelationship(DataphoraModel):
    """One entry of a resource ``relationships`` object.

    ``data`` holds the identifier, or the list of identifiers for
    to-many relationships such as a DOI's ``references`` and ``citations``.
    """

    data: JsonApiIdentifier | list[JsonApiIdentifier] | None = None
    links: dict[str, str] | None = None


class DataphoraResource(DataphoraModel):
    """A flattened JSON:API resource.

    A raw resource object ``{"id": ..., "type": ..., "attributes": {...},
    "relationships": {...}, "links": {...}}`` validates into one model whose
    fields are ``id``, the attributes at top level, and ``relationships`` and
    ``links`` as attributes of their own. Passing an already-flat dict (for
    example ``DataphoraDoi(doi="10.5438/0012")``) also works.
    """

    id: str
    type: str | None = None
    relationships: dict[str, JsonApiRelationship] | None = None
    links: dict[str, str] | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten_envelope(cls, data: object) -> object:
        """Merge the ``attributes`` dict of a raw resource into the top level."""
        if not isinstance(data, dict) or "attributes" not in data:
            return data
        flat = {key: value for key, value in data.items() if key != "attributes"}
        attributes = data["attributes"]
        if isinstance(attributes, dict):
            flat.update(attributes)
        return flat

    @field_validator("id", mode="before")
    @classmethod
    def _id_to_str(cls, value: object) -> str:
        """Normalize integer ids (some events arrive with numeric ids)."""
        return str(value)


def resource_ids(relationship: JsonApiRelationship | None) -> list[str]:
    """Return the ids a relationship points at, in order."""
    if relationship is None or relationship.data is None:
        return []
    data = relationship.data
    if isinstance(data, list):
        return [entry.id for entry in data if entry.id is not None]
    return [data.id] if data.id is not None else []


__all__ = [
    "JsonApiIdentifier",
    "JsonApiRelationship",
    "DataphoraModel",
    "DataphoraResource",
    "resource_ids",
]
