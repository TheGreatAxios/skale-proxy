import pytest
from aiohttp import web
from typing import Dict
from src.collector import get_chain_stats
from conftest import CHAIN_STATS, SAMPLE_METADATA, generate_sample_counter

pytestmark = pytest.mark.asyncio
pytest_plugins = ('pytest_asyncio',)

NETWORK = 'testnet'
CHAIN_NAME = 'testchain'


async def chain_stats_api(request):
    return web.json_response(CHAIN_STATS)


async def address_counter_api(request):
    address = request.match_info.get('address')
    if any(
        address in app['contracts']
        for chain in SAMPLE_METADATA.values()
        for app in chain['apps'].values()
    ):
        return web.json_response(generate_sample_counter())
    return web.json_response({}, status=404)


def create_app():
    app = web.Application()
    app.router.add_route('GET', '/api/v2/stats', chain_stats_api)
    app.router.add_route('GET', '/api/v2/addresses/{address}/counters', address_counter_api)
    return app


@pytest.fixture
def mock_explorer_url(monkeypatch):
    def mock_get_explorer_url(network, chain_name):
        return ''

    monkeypatch.setattr('src.explorer._get_explorer_url', mock_get_explorer_url)


async def test_get_chain_stats(
    mock_chain_stats_data: Dict, aiohttp_client, mock_explorer_url
) -> None:
    client = await aiohttp_client(create_app())
    result = await get_chain_stats(client, NETWORK, CHAIN_NAME)
    assert isinstance(result, dict)
    assert result == mock_chain_stats_data
