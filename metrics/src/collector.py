#   -*- coding: utf-8 -*-
#
#   This file is part of portal-metrics
#
#   Copyright (C) 2024 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
from aiohttp import ClientError, ClientSession

from src.explorer import get_address_counters_url, get_chain_stats
from src.gas import calc_avg_gas_price
from src.db import update_transaction_counts, get_address_transaction_counts
from src.utils import transform_to_dict, decimal_default
from src.config import (
    METRICS_FILEPATH,
    API_ERROR_TIMEOUT,
    API_ERROR_RETRIES,
    GITHUB_RAW_URL,
    OFFCHAIN_KEY,
)
from src.metrics_types import AddressCounter, AddressCountersMap, MetricsData, ChainMetrics


logger = logging.getLogger(__name__)


def get_metadata_url(network_name: str) -> str:
    return f'{GITHUB_RAW_URL}/skalenetwork/skale-network/master/metadata/{network_name}/chains.json'


async def download_metadata(session, network_name: str) -> Dict:
    url = get_metadata_url(network_name)
    async with session.get(url) as response:
        metadata_srt = await response.text()
        return json.loads(metadata_srt)


def get_empty_address_counter() -> AddressCounter:
    return {
        'gas_usage_count': '0',
        'token_transfers_count': '0',
        'transactions_count': '0',
        'validations_count': '0',
        'transactions_last_day': 0,
        'transactions_last_7_days': 0,
        'transactions_last_30_days': 0,
    }


async def fetch_address_data(session: ClientSession, url: str) -> AddressCounter:
    async with session.get(url) as response:
        if response.status == 404:
            data = await response.json()
            if data.get('message') == 'Not found':
                logger.warning(f'Address not found at {url}. Returning empty counter.')
                return get_empty_address_counter()
        response.raise_for_status()
        return await response.json()


async def get_address_counters(
    session: ClientSession, network: str, chain_name: str, address: str
) -> AddressCounter:
    url = get_address_counters_url(network, chain_name, address)
    for attempt in range(API_ERROR_RETRIES):
        try:
            data = await fetch_address_data(session, url)

            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            transactions_last_day = await get_address_transaction_counts(
                address, yesterday, yesterday
            )
            transactions_last_7_days = await get_address_transaction_counts(
                address, week_ago, yesterday
            )
            transactions_last_30_days = await get_address_transaction_counts(
                address, month_ago, yesterday
            )

            data['transactions_last_day'] = transactions_last_day
            data['transactions_last_7_days'] = transactions_last_7_days
            data['transactions_last_30_days'] = transactions_last_30_days

            return data
        except ClientError as e:
            if attempt < API_ERROR_RETRIES - 1:
                logger.warning(f'Attempt {attempt + 1} failed for {url}. Retrying... Error: {e}')
                await asyncio.sleep(API_ERROR_TIMEOUT)
            else:
                logger.error(f'All attempts failed for {url}. Error: {e}')
                raise
    raise Exception(f'Failed to fetch data for {url}')


async def get_all_address_counters(session, network, chain_name, addresses) -> AddressCountersMap:
    results = [
        await get_address_counters(session, network, chain_name, address) for address in addresses
    ]
    return dict(zip(addresses, results))


async def fetch_counters_for_app(
    session, network_name, chain_name, app_name, app_info
) -> Tuple[str, Optional[AddressCountersMap]]:
    logger.info(f'fetching counters for app {app_name}')
    if 'contracts' in app_info:
        counters = await get_all_address_counters(
            session, network_name, chain_name, app_info['contracts']
        )
        return app_name, counters
    return app_name, None


async def fetch_counters_for_apps(session, chain_info, network_name, chain_name):
    tasks = [
        fetch_counters_for_app(session, network_name, chain_name, app_name, app_info)
        for app_name, app_info in chain_info['apps'].items()
    ]
    return await asyncio.gather(*tasks)


async def collect_metrics(network_name: str) -> MetricsData:
    async with aiohttp.ClientSession() as session:
        metadata = await download_metadata(session, network_name)
        metrics: Dict[str, ChainMetrics] = {}

        for chain_name, chain_info in metadata.items():
            if chain_name == OFFCHAIN_KEY:
                continue
            chain_stats = await get_chain_stats(session, network_name, chain_name)
            apps_counters = None

            if 'apps' in chain_info:
                apps_counters = await fetch_counters_for_apps(
                    session, chain_info, network_name, chain_name
                )

            metrics[chain_name] = {
                'chain_stats': chain_stats,
                'apps_counters': transform_to_dict(apps_counters),
            }

            if apps_counters:
                for app_name, app_counters in metrics[chain_name]['apps_counters'].items():
                    for address, contract_data in app_counters.items():
                        await update_transaction_counts(
                            chain_name, app_name, address, contract_data
                        )

        data: MetricsData = {
            'metrics': metrics,
            'gas': int(calc_avg_gas_price()),
            'last_updated': int(datetime.now().timestamp()),
        }

        logger.info(f'Saving metrics to {METRICS_FILEPATH}')
        with open(METRICS_FILEPATH, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True, default=decimal_default)

        return data
