import pytest
from typing import Dict
from src.collector import get_chain_stats, fetch_address_data
from conftest import TEST_NETWORK, TEST_CHAIN

pytestmark = pytest.mark.asyncio
pytest_plugins = ('pytest_asyncio',)


async def test_get_chain_stats(mock_chain_stats_data: Dict, client, mock_explorer_url) -> None:
    result = await get_chain_stats(client, TEST_NETWORK, TEST_CHAIN)
    assert isinstance(result, dict)
    assert result == mock_chain_stats_data


async def test_fetch_address_data(client, mock_explorer_url) -> None:
    result = await fetch_address_data(client, '/api/v2/addresses/0x1234/counters')
    assert isinstance(result, dict)
    assert result['gas_usage_count'] == '16935'
    assert result['token_transfers_count'] == '174'
    assert result['transactions_count'] == '1734'
    assert result['validations_count'] == '22'
