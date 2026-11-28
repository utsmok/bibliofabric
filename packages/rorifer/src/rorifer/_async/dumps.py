"""ROR data dumps hosted on Zenodo: list, pick, and download."""

from pathlib import Path

import httpx
from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..dialect import ROR_ZENODO_API_BASE_URL, ROR_ZENODO_COMMUNITY
from ..models import RorDump

#: Records fetched to find the newest dump; Zenodo lists by last update,
#: not by publication date.
_LATEST_LOOKUP_SIZE = 25


class DumpsClient:
    """Access to the ROR data dumps in the ``ror-data`` Zenodo community."""

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def list(self, *, limit: int = 5) -> list[RorDump]:
        """Return the most recently updated dump records.

        Args:
            limit: Number of Zenodo records to return. Zenodo orders them by
                last update, not by publication date.
        """
        if limit <= 0:
            raise ConfigurationError(f"limit must be positive, got {limit}.")
        response = await self._client.request(
            "GET",
            f"{ROR_ZENODO_API_BASE_URL}/records",
            params={
                "q": f"communities:{ROR_ZENODO_COMMUNITY}",
                "sort": "mostrecent",
                "size": limit,
                "type": "dataset",
            },
        )
        body = self._client.parse_json(response)
        hits = body.get("hits") if isinstance(body, dict) else None
        records = hits.get("hits") if isinstance(hits, dict) else None
        return [
            validate_model(
                RorDump,
                record,
                request=getattr(response, "request", None),
                response=response,
            )
            for record in records or []
            if isinstance(record, dict)
        ]

    async def latest(self) -> RorDump:
        """Return the dump with the newest publication date."""
        dumps = await self.list(limit=_LATEST_LOOKUP_SIZE)
        if not dumps:
            raise ConfigurationError(
                f"Zenodo returned no records for the {ROR_ZENODO_COMMUNITY} community."
            )
        return max(dumps, key=lambda dump: dump.publication_date or "")

    async def download(self, dump: RorDump, dest: Path | str) -> Path:
        """Stream the dump zip to ``dest`` and return the path.

        Creates parent directories and overwrites an existing file.
        """
        url = dump.zip_url
        if not url:
            raise ConfigurationError(
                f"ROR dump {dump.record_id} has no downloadable zip file."
            )
        target = Path(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        async with self._client.stream("GET", url, follow_redirects=True) as response:
            await self._copy_to(response, target)
        return target

    @staticmethod
    async def _copy_to(response: httpx.Response, target: Path) -> None:
        """Write a streamed response body to ``target`` chunk by chunk."""
        with target.open("wb") as handle:
            async for chunk in response.aiter_bytes():
                handle.write(chunk)


__all__ = ["DumpsClient"]
