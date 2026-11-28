"""Client for the WikibaseLexeme REST API.

The lexeme routes live under ``/w/rest.php/wikibaselexeme/v0`` (the same
routes under ``wikibase/v1`` answer 404, verified 2026-11-27). Only the
lexeme entity route exists; per-form and per-sense routes answer
``rest-no-match``, so forms and senses come inside the lexeme payload.
"""

from bibliofabric import BaseApiClient, validate_model

from ..dialect import REST_LEXEME_PREFIX
from ..ids import normalize_wikidata_id
from ..models import RestLexeme


class LexemesClient:
    """Client for the REST lexeme routes."""

    def __init__(self, client: BaseApiClient) -> None:
        """Build the resource client on a ``QuidditaClient``."""
        self._client = client

    async def get(self, id: str) -> RestLexeme:
        """Return the full REST lexeme for ``id`` (lemmas, forms, senses)."""
        normalized = normalize_wikidata_id(id)
        if normalized[0] != "L":
            raise ValueError(f"Expected a lexeme id such as 'L2', got {id!r}.")
        response = await self._client.request(
            "GET", f"{REST_LEXEME_PREFIX}/entities/lexemes/{normalized}"
        )
        return validate_model(RestLexeme, self._client.parse_json(response))


__all__ = ["LexemesClient"]
