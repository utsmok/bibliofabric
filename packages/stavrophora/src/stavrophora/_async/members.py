"""Members resource: ``/members`` and the ``/members/{id}/works`` scope."""

from urllib.parse import quote

from ..filters import MemberFilters
from ..models import Member
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class MembersResource(CrossrefResourceClient[Member]):
    """Typed client for the Crossref ``/members`` routes.

    Accepts plain ``query`` plus the member-specific filters (``prefix``,
    ``backfile-doi-count``, ``current-doi-count``).
    """

    path = "members"
    model = Member
    filters_model = MemberFilters
    supports_filter = True

    def works(self, member_id: str | int) -> ScopedWorksResource:
        """Return a works client bound to ``members/{id}/works``."""
        member_id = quote(str(member_id).strip(), safe="")
        return ScopedWorksResource(self._client, path=f"members/{member_id}/works")
