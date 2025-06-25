"""AIREloom: A Python client for the OpenAIRE Graph API."""

__version__ = "1.0.0"

# Import Exceptions from bibliofabric
from bibliofabric.exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

# Import main client class
from .client import AireloomClient

# Re-export key models from the models subpackage
from .models import (
    ApiResponse,
    BaseEntity,
    DataSource,
    Header,
    Organization,
    Project,
    ResearchProduct,
    ScholixRelationship,
)

# Import main session class
from .session import AireloomSession

__all__ = [
    # Core Client/Session
    "AireloomClient",
    "AireloomSession",
    # Core Exceptions
    "BibliofabricError",
    "APIError",
    "AuthError",
    "ConfigurationError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    # Key Models (consider reducing if needed)
    "ApiResponse",
    "BaseEntity",
    "DataSource",
    "Header",
    "Organization",
    "Project",
    "ResearchProduct",
    "ScholixRelationship",
]
