"""Live smoke tests for the sync client, one per operation family.

Deselected by default (``-m 'not live_api'`` in ``addopts``). Run them with
``uv run pytest -m live_api packages/aireloom``; anonymous access works for
these read-only calls. The async twins live in ``tests/test_live_smoke.py``.
"""

import pytest
from aireloom import AireloomSyncClient

pytestmark = pytest.mark.live_api

DOI = "10.1038/nature12373"


def test_sync_search():
    with AireloomSyncClient() as aireloom:
        page = aireloom.research_products.search(page_size=1)
    assert page.total and page.results
    assert page.results[0].id


def test_sync_get_by_id():
    with AireloomSyncClient() as aireloom:
        page = aireloom.research_products.search(query=DOI, page_size=1)
        product = page.results[0]
        fetched = aireloom.research_products.get(product.id)
    assert fetched.id == product.id


def test_sync_iterate():
    records = []
    with AireloomSyncClient() as aireloom:
        for record in aireloom.research_products.iterate(page_size=10):
            records.append(record)
            if len(records) == 3:
                break
    assert len(records) == 3


def test_sync_batch_get_by_doi():
    with AireloomSyncClient() as aireloom:
        products = aireloom.research_products.batch_get_by_doi(
            ["10.5281/zenodo.15069438", "10.1038/s41586-023-06221-2"]
        )
    assert products
    for product in products.values():
        assert product.id
