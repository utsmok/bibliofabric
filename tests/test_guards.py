"""Client-side guards that mirror Crossref's 400 responses, and error messages."""

import pytest
from bibliofabric.exceptions import ConfigurationError

from stavrophora import FunderFilters, MemberFilters
from tests.conftest import works_envelope


@pytest.mark.parametrize(
    "sort", ["issued", "published", "published-print", "published-online"]
)
async def test_cursor_iteration_rejects_date_sorts(client, sort):
    with pytest.raises(ConfigurationError, match="Cursor iteration"):
        [item async for item in client.works.iterate(sort=sort)]


@pytest.mark.parametrize("sort", ["issued:desc", "published:asc"])
async def test_cursor_date_sort_error_names_the_sort(client, sort):
    with pytest.raises(ConfigurationError, match=sort.split(":")[0]):
        [item async for item in client.works.iterate(sort=sort)]


async def test_cursor_iteration_allows_citation_sort(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    items = [
        item async for item in client.works.iterate(sort="is-referenced-by-count:desc")
    ]
    assert items == []
    params = httpx_mock.get_requests()[0].url.params
    assert params["sort"] == "is-referenced-by-count"
    assert params["cursor"] == "*"


async def test_journals_reject_sort_and_select(httpx_mock, client):
    with pytest.raises(
        ConfigurationError, match="/journals route does not support sort"
    ):
        await client.journals.search(sort="score")
    with pytest.raises(
        ConfigurationError, match="/journals route does not support select"
    ):
        await client.journals.search(select=["title"])
    assert httpx_mock.get_requests() == []


async def test_types_reject_query_and_filter(httpx_mock, client):
    with pytest.raises(ConfigurationError, match="/types route does not support query"):
        await client.types.search(query="journal")
    with pytest.raises(
        ConfigurationError, match="/types route does not support filter"
    ):
        await client.types.search({"type": "journal-article"})


async def test_funders_reject_sort(httpx_mock, client):
    with pytest.raises(
        ConfigurationError, match="/funders route does not support sort"
    ):
        await client.funders.search(FunderFilters(location="Netherlands"), sort="score")


async def test_members_accept_their_own_filters(httpx_mock, client):
    httpx_mock.add_response(
        json={"status": "ok", "message": {"items": [], "total-results": 0}}
    )
    await client.members.search(MemberFilters(prefix="10.1038"))
    assert httpx_mock.get_requests()[0].url.params["filter"] == "prefix:10.1038"


async def test_prefixes_has_no_list_route(client):
    for call in (client.prefixes.search, client.prefixes.count):
        with pytest.raises(ConfigurationError, match="no /prefixes list route"):
            await call()
    with pytest.raises(ConfigurationError, match="no /prefixes list route"):
        [item async for item in client.prefixes.iterate()]
