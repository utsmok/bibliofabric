"""One redirect location of the proxy's ``action=showurls`` listing."""

from pydantic import BaseModel, ConfigDict


class RedirectLocation(BaseModel):
    """One ``location`` element of the proxy's redirect listing.

    ``href`` is the URL. The proxy sends ``mode="legacy"`` and a numeric
    ``weight`` for the landing page, ``http_role="conneg"`` and
    ``href_template`` for the registration agency's metadata server, and
    other attributes for the locations of a multiple-resolution DOI. Every
    attribute stays, as the string the proxy sends.
    """

    href: str
    mode: str | None = None
    weight: str | None = None
    http_role: str | None = None
    href_template: str | None = None

    model_config = ConfigDict(extra="allow")
