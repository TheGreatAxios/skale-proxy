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
from datetime import date, timedelta
from typing import List, Dict, Any
from decimal import Decimal

from peewee import fn, IntegrityError

from src.models import db, Address, TransactionCount
from src.config import NETWORK_NAME
from src.explorer import get_address_counters_url

logger = logging.getLogger(__name__)

TRANSACTION_COUNT_FIELD = 'transactions_count'
BACKFILL_DB_DAYS = 30


async def get_current_total_transactions(session, chain_name: str, address: str) -> int:
    url = get_address_counters_url(NETWORK_NAME, chain_name, address)
    async with session.get(url) as response:
        data = await response.json()
        return int(data.get('transactions_count', 0))


async def bootstrap_db(session, apps_data: Dict[str, Dict[str, List[str]]]) -> None:
    today = date.today()
    thirty_days_ago = today - timedelta(days=BACKFILL_DB_DAYS)
    with db.atomic():
        if Address.select().count() > 0:
            logger.info('Database is not empty. Skipping bootstrap.')
            return
        logger.info('Bootstrapping database with initial data...')
        for chain_name, chain_data in apps_data.items():
            for app_name, addresses in chain_data.items():
                for address in addresses:
                    logger.info(f'Bootstrapping data for {address} on {chain_name}...')
                    addr = Address.create(chain_name=chain_name, address=address, app_name=app_name)
                    total_transactions = await get_current_total_transactions(
                        session, chain_name, address
                    )
                    for day in range(BACKFILL_DB_DAYS):
                        current_date = thirty_days_ago + timedelta(days=day)
                        try:
                            TransactionCount.create(
                                address=addr,
                                date=current_date,
                                total_transactions=total_transactions,
                                daily_transactions=0,
                            )
                        except IntegrityError:
                            logger.warning(
                                f'Record already exists for {address} on {current_date}. Skipping.'
                            )
        logger.info('Database bootstrap completed successfully.')


async def update_transaction_counts(
    chain_name: str, app_name: str, address: str, contract_data: Dict[str, Any]
) -> None:
    today = date.today()

    with db.atomic():
        addr, _ = Address.get_or_create(chain_name=chain_name, address=address, app_name=app_name)

        total_transactions = int(contract_data.get(TRANSACTION_COUNT_FIELD, 0))

        yesterday_count = (
            TransactionCount.select(fn.MAX(TransactionCount.total_transactions))
            .where((TransactionCount.address == addr) & (TransactionCount.date < today))
            .scalar()
        )

        if yesterday_count is None:
            yesterday_count = 0

        daily_transactions = total_transactions - yesterday_count

        TransactionCount.replace(
            address=addr,
            date=today,
            total_transactions=total_transactions,
            daily_transactions=daily_transactions,
        ).execute()

        logger.info(
            f'Updated transaction count for {address} on {today}: '
            f'total={total_transactions}, daily={daily_transactions}'
        )


async def get_address_transaction_counts(address: str, start_date: date, end_date: date) -> int:
    with db.atomic():
        result = (
            TransactionCount.select(fn.SUM(TransactionCount.daily_transactions))
            .where(
                (TransactionCount.address == Address.get(address=address))
                & (TransactionCount.date.between(start_date, end_date))
            )
            .scalar()
            or 0
        )
        return int(result) if isinstance(result, Decimal) else result
