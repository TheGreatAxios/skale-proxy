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
from datetime import date
from typing import Any, Dict

from peewee import fn

from src.models import db, Address, TransactionCount


logger = logging.getLogger(__name__)

TRANSACTION_COUNT_FIELD = "transactions_count"


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
            f"Updated transaction count for {address} on {today}: "
            f"total={total_transactions}, daily={daily_transactions}"
        )
