"""Internal redaction helpers for logs and exception messages."""

import re
from collections.abc import Collection, Mapping

_SENSITIVE_QUERY_PARAMETER = re.compile(
    r"([?&](?:access[_-]?token|api[_-]?key|client[_-]?secret|"
    r"password|secret|token|key|sig|signature)=)([^&#\s]*)",
    re.IGNORECASE,
)

_SENSITIVE_HEADER_MARKERS = ("authorization", "token", "key", "secret", "cookie")

__all__ = ["sanitize_headers", "sanitize_url"]


def sanitize_url(
    url: object,
    *,
    extra_params: Collection[str] = (),
) -> str:
    """Redact credential query parameters from a URL before it is logged.

    ``extra_params`` names additional query parameters (for example custom
    parameters declared by an auth strategy) to redact alongside the built-in
    defaults.
    """
    redacted = _SENSITIVE_QUERY_PARAMETER.sub(r"\1***", str(url))
    custom = tuple(param for param in extra_params if param)
    if not custom:
        return redacted
    pattern = re.compile(
        r"([?&](?:" + "|".join(re.escape(name) for name in custom) + r")=)([^&#\s]*)",
        re.IGNORECASE,
    )
    return pattern.sub(r"\1***", redacted)


def sanitize_headers(
    headers: Mapping[str, str],
    *,
    extra_headers: Collection[str] = (),
) -> dict[str, str]:
    """Return a copy of ``headers`` with credential values replaced by ``***``.

    ``mailto`` and other contact parameters are not considered secrets and are
    left in place. ``extra_headers`` adds case-insensitive header names to
    redact alongside the built-in markers.
    """
    extra_lower = {name.lower() for name in extra_headers if name}
    redacted: dict[str, str] = {}
    for name, value in headers.items():
        lowered = name.lower()
        redacted[name] = (
            "***"
            if lowered in extra_lower
            or any(marker in lowered for marker in _SENSITIVE_HEADER_MARKERS)
            else value
        )
    return redacted
