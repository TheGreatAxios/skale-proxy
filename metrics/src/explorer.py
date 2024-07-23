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

import logging
import requests
from typing import Any

from config import BASE_EXPLORER_URLS, HTTPS_PREFIX

logger = logging.getLogger(__name__)


def _get_explorer_url(network, chain_name):
    explorer_base_url = BASE_EXPLORER_URLS[network]
    return HTTPS_PREFIX + chain_name + '.' + explorer_base_url


def get_chain_stats(network: str, chain_name: str) -> Any:
    try:
        explorer_url = _get_explorer_url(network, chain_name)
        response = requests.get(f'{explorer_url}/api/v2/stats')
        return response.json()
    except Exception as e:
        logger.exception(e)
        logger.error(f'Failed to get chain stats: {e}')
        return None


def get_address_counters_url(network: str, chain_name: str, address: str) -> str:
    explorer_url = _get_explorer_url(network, chain_name)
    return f'{explorer_url}/api/v2/addresses/{address}/counters'
