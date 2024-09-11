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

import sys
import asyncio
import logging
from time import sleep
from datetime import datetime

from src.logs import init_default_logger
from src.collector import collect_metrics
from src.config import (
    NETWORK_NAME,
    PROXY_ENDPOINTS,
    METRICS_CHECK_INTERVAL,
    METRICS_ERROR_CHECK_INTERVAL,
)
from src.models import db

logger = logging.getLogger(__name__)


def run_migrations():
    logger.info('Running database migrations...')
    try:
        from models import Address, TransactionCount

        with db:
            db.create_tables([Address, TransactionCount])
        logger.info('Database migrations completed successfully.')
    except Exception as e:
        logger.error(f'Error running migrations: {e}')
        sys.exit(1)


def run_metrics_loop():
    if NETWORK_NAME not in PROXY_ENDPOINTS:
        logger.error(f'Unsupported network: {NETWORK_NAME}')
        sys.exit(1)

    logger.info(f'Starting metrics collection loop for network: {NETWORK_NAME}')
    last_run_date = None

    while True:
        current_date = datetime.now().date()

        if last_run_date is None or current_date > last_run_date:
            logger.info(f'Daily metrics collection started for {NETWORK_NAME}...')
            try:
                with db.connection_context():
                    asyncio.run(collect_metrics(NETWORK_NAME))
                last_run_date = current_date
                logger.info(f'Daily metrics collection completed for {NETWORK_NAME}.')
                logger.info(f'Sleeping for {METRICS_CHECK_INTERVAL} seconds.')
                sleep(METRICS_CHECK_INTERVAL)
            except Exception as e:
                logger.exception(f'Error during metrics collection for {NETWORK_NAME}: {e}')
                logger.info(f'Sleeping for {METRICS_ERROR_CHECK_INTERVAL} seconds after error.')
                sleep(METRICS_ERROR_CHECK_INTERVAL)
        else:
            logger.info(
                f'Not time for collection yet. \
                Last run: {last_run_date}, Current date: {current_date}'
            )
            logger.info(f'Sleeping for {METRICS_CHECK_INTERVAL} seconds.')
            sleep(METRICS_CHECK_INTERVAL)


def wait_for_db():
    max_retries = 30
    retry_interval = 2

    for _ in range(max_retries):
        try:
            db.connect()
            db.close()
            logger.info('Successfully connected to the database.')
            return
        except Exception as e:
            logger.exception(e)
            logger.warning(f'Database connection failed. Retrying in {retry_interval} seconds...')
            sleep(retry_interval)

    logger.error('Failed to connect to the database after multiple attempts.')
    sys.exit(1)


if __name__ == '__main__':
    init_default_logger()
    logger.info(f'Starting metrics collector for network: {NETWORK_NAME}')
    wait_for_db()
    run_migrations()
    run_metrics_loop()
