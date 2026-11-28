"""Client for the Semantic Scholar Datasets API."""

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..dialect import SEMANTICSCHOLAR_DATASETS_BASE_URL
from ..models import DatasetDiffList, DatasetMetadata, Release
from .resources import id_path


class DatasetsClient:
    """Client for the ``/datasets/v1`` routes.

    A release is a dated snapshot of the whole Academic Graph. Listing
    releases and reading a release's dataset summaries works without a
    key. Reading a dataset's file URLs and fetching diffs need an API
    key and answer HTTP 401 without one.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def releases(self) -> list[str]:
        """Return every release id (``GET /release``).

        The ids are date strings such as ``2026-11-24``, oldest first.
        """
        response = await self._client.request(
            "GET", f"{SEMANTICSCHOLAR_DATASETS_BASE_URL}/release"
        )
        body = self._client.parse_json(response)
        if not isinstance(body, list):
            raise ConfigurationError(
                "GET /datasets/v1/release answered without a list."
            )
        return [str(item) for item in body if item is not None]

    async def release(self, release_id: str = "latest") -> Release:
        """Return one release with its dataset summaries.

        ``release_id`` is a date string or ``latest``.
        """
        response = await self._client.request(
            "GET",
            f"{SEMANTICSCHOLAR_DATASETS_BASE_URL}/release/{id_path(release_id)}",
        )
        body = self._client.parse_json(response)
        release = validate_model(
            Release,
            body,
            request=getattr(response, "request", None),
            response=response,
        )
        if release.release_id is None:
            release.release_id = release_id
        return release

    async def latest(self) -> Release:
        """Return the newest release with its dataset summaries."""
        return await self.release("latest")

    async def dataset(
        self,
        name: str,
        *,
        release_id: str = "latest",
    ) -> DatasetMetadata:
        """Return one dataset of one release, with its file URLs.

        ``files`` holds temporary pre-signed download links. This route
        needs an API key.
        """
        response = await self._client.request(
            "GET",
            f"{SEMANTICSCHOLAR_DATASETS_BASE_URL}/release/{id_path(release_id)}"
            f"/dataset/{id_path(name)}",
        )
        body = self._client.parse_json(response)
        return validate_model(
            DatasetMetadata,
            body,
            request=getattr(response, "request", None),
            response=response,
        )

    async def diffs(
        self,
        dataset_name: str,
        start_release: str,
        end_release: str,
    ) -> DatasetDiffList:
        """Return the diffs between two releases of one dataset.

        Applying ``updateFiles`` and ``deleteFiles`` in order brings a
        local copy from ``start_release`` to ``end_release``. This route
        needs an API key.
        """
        response = await self._client.request(
            "GET",
            f"{SEMANTICSCHOLAR_DATASETS_BASE_URL}/diffs/{id_path(start_release)}"
            f"/to/{id_path(end_release)}/{id_path(dataset_name)}",
        )
        body = self._client.parse_json(response)
        return validate_model(
            DatasetDiffList,
            body,
            request=getattr(response, "request", None),
            response=response,
        )


__all__ = ["DatasetsClient"]
