"""Bibliofabric: Generic framework for building modern asynchronous API clients.

This package provides the core infrastructure for building bibliometric and scholarly
data retrieval clients. It includes generic HTTP client functionality, authentication
strategies, caching, rate limiting, and reusable resource mixins.

The framework is designed to be extended by specific API client implementations
(like aireloom for OpenAIRE) while centralizing common functionality.
"""

__version__ = "0.1.0"
__author__ = "Samuel Mok"
__email__ = "s.mok@utwente.nl"

# Import core modules for easy access
from . import auth, client, config, exceptions, log_config, models, resources, types

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "auth",
    "client",
    "config",
    "exceptions",
    "log_config",
    "models",
    "resources",
    "types",
]
