# https://graph.openaire.eu/docs/data-model/entities/data-source
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field  # Added ConfigDict

from .base import ApiResponse, BaseEntity
from .research_product import Container

# Type literals for restricted values
AccessRightType = Literal["open", "restricted", "closed"]
DatabaseRestrictionType = Literal["feeRequired", "registration", "other"]


# Base classes for controlled fields
class ControlledField(BaseModel):
    """Represents a controlled vocabulary field with scheme and value."""

    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


# Main DataSource model
class DataSource(BaseEntity):
    """Model representing an OpenAIRE Data Source entity."""

    originalIds: list[str] | None = Field(default_factory=list)
    pids: list[ControlledField] | None = Field(default_factory=list)
    type: ControlledField | None = None
    openaireCompatibility: str | None = None
    officialName: str | None = None
    englishName: str | None = None
    websiteUrl: str | None = None
    logoUrl: str | None = None
    dateOfValidation: str | None = None
    description: str | None = None
    subjects: list[str] | None = Field(default_factory=list)
    languages: list[str] | None = Field(default_factory=list)
    contentTypes: list[str] | None = Field(default_factory=list)
    releaseStartDate: str | None = None
    releaseEndDate: str | None = None
    accessRights: AccessRightType | None = None
    uploadRights: AccessRightType | None = None
    databaseAccessRestriction: DatabaseRestrictionType | None = None
    dataUploadRestriction: str | None = None
    versioning: bool | None = None
    citationGuidelineUrl: str | None = None
    pidSystems: str | None = None
    certificates: str | None = None
    policies: list[str] | None = Field(default_factory=list)
    missionStatementUrl: str | None = None
    # Added based on documentation/analysis
    journal: Container | None = None

    model_config = ConfigDict(extra="allow")


# Define the specific response type for data sources
DataSourceResponse = ApiResponse[DataSource]
