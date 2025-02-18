import pytest
from unittest.mock import patch
from typing import Dict
from src.collector import get_chain_stats, fetch_address_data, get_db_counts
from conftest import TEST_NETWORK, TEST_CHAIN, TEST_ADDRESS, TEST_APP

pytestmark = pytest.mark.asyncio
pytest_plugins = ('pytest_asyncio',)


async def test_get_chain_stats(mock_chain_stats_data: Dict, client, mock_explorer_url) -> None:
    result = await get_chain_stats(client, TEST_NETWORK, TEST_CHAIN)
    assert isinstance(result, dict)
    assert result == mock_chain_stats_data


async def test_fetch_address_data_success(
    client, mock_explorer_url, address_data: Dict[str, str], mock_db_data: Dict[str, int]
) -> None:
    with (
        patch('src.collector.update_transaction_counts') as mock_update,
        patch('src.collector.get_address_transaction_counts') as mock_get_counts,
    ):
        mock_get_counts.side_effect = [
            mock_db_data['transactions_today'],
            mock_db_data['transactions_last_7_days'],
            mock_db_data['transactions_last_30_days'],
        ]

        result = await fetch_address_data(
            client, '/api/v2/addresses/0x1234/counters', TEST_CHAIN, TEST_APP, TEST_ADDRESS
        )

        assert isinstance(result, dict)
        assert result['gas_usage_count'] == address_data['gas_usage_count']
        assert result['token_transfers_count'] == address_data['token_transfers_count']
        assert result['transactions_count'] == address_data['transactions_count']
        assert result['validations_count'] == address_data['validations_count']
        assert result['transactions_today'] == mock_db_data['transactions_today']
        assert result['transactions_last_7_days'] == mock_db_data['transactions_last_7_days']
        assert result['transactions_last_30_days'] == mock_db_data['transactions_last_30_days']
        mock_update.assert_called_once()


async def test_get_address_counters(mock_today, sample_counters, address_data) -> None:
    result = await get_db_counts(address_data, TEST_CHAIN, TEST_APP, TEST_ADDRESS)
    assert isinstance(result, dict)
    assert result['gas_usage_count'] == address_data['gas_usage_count']
    assert result['token_transfers_count'] == address_data['token_transfers_count']
    assert result['transactions_count'] == address_data['transactions_count']
    assert result['validations_count'] == address_data['validations_count']
    assert 'transactions_today' in result
    assert 'transactions_last_7_days' in result
    assert 'transactions_last_30_days' in result

    current_day_counters = sample_counters['addresses'][0]['daily_data'][-1]

    current_day_counters['transactions_today'] = result['transactions_today']
    current_day_counters['transactions_last_7_days'] = result['transactions_last_7_days']
    current_day_counters['transactions_last_30_days'] = result['transactions_last_30_days']
