"""Pydantic models for OpenAIRE API entities and Scholix links."""

from bibliofabric import SafeList, SafeStr

from .base import (
    BaseEntity,
    CfHbKeyValue,
    CodeLabel,
    DsRef,
    FundingFunder,
    FundingHierarchy,
    FundingJurisdiction,
    FundingLevel,
    Pid,
    Provenance,
    RelatedRecordHeader,
    TypedPid,
)
from .data_source import DataSource
from .organization import Country, Organization
from .person import Person
from .project import (
    Funding,
    FundingStream,
    Grant,
    H2020Programme,
    Project,
    ProjectLink,
)
from .relation import (
    EntityRef,
    Identifier,
    Node,
    Relation,
    RelationInfo,
    RelType,
)
from .research_product import (
    Author,
    AuthorPid,
    Instance,
    ProductCommunity,
    ProductOrganization,
    ProductProject,
    RelatedRecord,
    ResearchProduct,
    Subject,
)
from .scholix import (
    ScholixCreator,
    ScholixEntity,
    ScholixIdentifier,
    ScholixLinkProvider,
    ScholixPublisher,
    ScholixRelationship,
)

__all__ = [
    "Author",
    "AuthorPid",
    "BaseEntity",
    "CfHbKeyValue",
    "CodeLabel",
    "Country",
    "DataSource",
    "DsRef",
    "EntityRef",
    "Funding",
    "FundingFunder",
    "FundingHierarchy",
    "FundingJurisdiction",
    "FundingLevel",
    "FundingStream",
    "Grant",
    "H2020Programme",
    "Identifier",
    "Instance",
    "Node",
    "Organization",
    "Person",
    "Pid",
    "ProductCommunity",
    "ProductOrganization",
    "ProductProject",
    "Project",
    "ProjectLink",
    "Provenance",
    "RelatedRecord",
    "RelatedRecordHeader",
    "Relation",
    "RelationInfo",
    "RelType",
    "ResearchProduct",
    "SafeList",
    "SafeStr",
    "ScholixCreator",
    "ScholixEntity",
    "ScholixIdentifier",
    "ScholixLinkProvider",
    "ScholixPublisher",
    "ScholixRelationship",
    "Subject",
    "TypedPid",
]
