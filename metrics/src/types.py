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

from typing import TypedDict, Optional, Dict, NewType


class AddressCounter(TypedDict):
    gas_usage_count: str
    token_transfers_count: str
    transactions_count: str
    validations_count: str


AddressType = NewType("Address", str)
AddressCountersMap = Dict[AddressType, AddressCounter]


class GasPrices(TypedDict):
    average: float
    fast: float
    slow: float


class ChainStats(TypedDict):
    average_block_time: float
    coin_image: Optional[str]
    coin_price: Optional[float]
    coin_price_change_percentage: Optional[float]
    gas_price_updated_at: str
    gas_prices: GasPrices
    gas_prices_update_in: int
    gas_used_today: str
    market_cap: str
    network_utilization_percentage: float
    static_gas_price: Optional[float]
    total_addresses: str
    total_blocks: str
    total_gas_used: str
    total_transactions: str
    transactions_today: str
    tvl: Optional[float]
