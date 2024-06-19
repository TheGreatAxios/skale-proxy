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
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests

from explorer import get_address_counters_url, get_chain_stats
from gas import calc_avg_gas_price
from config import METRICS_FILEPATH

logger = logging.getLogger(__name__)


def get_metadata_url(network_name: str):
    return f'https://raw.githubusercontent.com/skalenetwork/skale-network/master/metadata/{network_name}/chains.json' # noqa


def download_metadata(network_name: str):
    url = get_metadata_url(network_name)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


async def get_address_counters(session, network, chain_name, address):
    url = get_address_counters_url(network, chain_name, address)
    async with session.get(url) as response:
        return await response.json()


async def get_all_address_counters(network, chain_name, addresses):
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for address in addresses:
            tasks.append(get_address_counters(session, network, chain_name, address))

        responses = await asyncio.gather(*tasks)

        for address, response in zip(addresses, responses):
            results[address] = response

    return results


async def _fetch_counters_for_app(network_name, chain_name, app_name, app_info):
    logger.info(f'fetching counters for app {app_name}')
    if 'contracts' in app_info:
        counters = await get_all_address_counters(network_name, chain_name, app_info['contracts'])
        return app_name, counters
    return app_name, None


async def fetch_counters_for_apps(chain_info, network_name, chain_name):
    tasks = []
    for app_name, app_info in chain_info['apps'].items():
        task = _fetch_counters_for_app(network_name, chain_name, app_name, app_info)
        tasks.append(task)
    return await asyncio.gather(*tasks)


def transform_to_dict(apps_counters: List[Tuple[str, Any]] | None) -> Dict[str, Any]:
    if not apps_counters:
        return {}
    results = {}
    for app_name, counters in apps_counters:
        results[app_name] = counters
    return results


def collect_metrics(network_name: str):
    metadata = download_metadata(network_name)
    metrics = {}
    for chain_name, chain_info in metadata.items():
        apps_counters = None
        chain_stats = get_chain_stats(network_name, chain_name)
        if 'apps' in chain_info:
            apps_counters = asyncio.run(
                fetch_counters_for_apps(chain_info, network_name, chain_name))
        metrics[chain_name] = {
            'chain_stats': chain_stats,
            'apps_counters': transform_to_dict(apps_counters),
        }
    data = {
        'metrics': metrics,
        'gas': int(calc_avg_gas_price()),
        'last_updated': int(datetime.now().timestamp())
    }
    logger.info(f'Saving metrics to {METRICS_FILEPATH}')
    with open(METRICS_FILEPATH, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
