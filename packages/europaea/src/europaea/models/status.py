"""Pydantic models for the article status monitor route."""

from pydantic import BaseModel, ConfigDict, Field


class ArticleStatusInput(BaseModel):
    """One source and external id pair of a status update query."""

    model_config = ConfigDict(extra="allow")

    src: str | None = None
    ext_id: str | None = Field(None, alias="extId")


class StatusUpdateRequest(BaseModel):
    """The JSON request body of a status update query (``ids``)."""

    model_config = ConfigDict(extra="allow")

    ids: list[ArticleStatusInput] | None = None


class StatusNotFound(BaseModel):
    """One source and external id pair the status monitor could not find."""

    model_config = ConfigDict(extra="allow")

    src: str | None = None
    ext_id: str | None = Field(None, alias="extId")


class StatusUpdateMetrics(BaseModel):
    """The metrics block of a status update answer (``metrics``)."""

    model_config = ConfigDict(extra="allow")

    articles_queried: int | None = Field(None, alias="articlesQueried")
    articles_found_in_the_database: int | None = Field(
        None, alias="articlesFoundInTheDatabase"
    )
    articles_without_status_update: int | None = Field(
        None, alias="articlesWithoutStatusUpdate"
    )
    articles_with_status_update: int | None = Field(
        None, alias="articlesWithStatusUpdate"
    )
    articles_not_found: list[StatusNotFound] | None = Field(
        None, alias="articlesNotFound"
    )


class StatusUpdateLink(BaseModel):
    """One related resource link of an article with status updates."""

    model_config = ConfigDict(extra="allow")

    rel: str | None = None
    href: str | None = None


class StatusUpdateArticle(BaseModel):
    """One article that carries status updates in the answer list."""

    model_config = ConfigDict(extra="allow")

    src: str | None = None
    ext_id: str | None = Field(None, alias="ext_ID")
    title: str | None = None
    first_publish_date: str | None = Field(None, alias="firstPublishDate")
    status_updates: list[str] | None = Field(None, alias="statusUpdates")
    links: list[StatusUpdateLink] | None = None


class StatusUpdateResponse(BaseModel):
    """The answer of ``POST /status-update-search``."""

    model_config = ConfigDict(extra="allow")

    metrics: StatusUpdateMetrics | None = None
    articles_with_status_update: list[StatusUpdateArticle] | None = Field(
        None, alias="articlesWithStatusUpdate"
    )


__all__ = [
    "ArticleStatusInput",
    "StatusNotFound",
    "StatusUpdateArticle",
    "StatusUpdateLink",
    "StatusUpdateMetrics",
    "StatusUpdateRequest",
    "StatusUpdateResponse",
]
