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
import logging
from time import sleep

from logs import init_default_logger
from collector import collect_metrics
from config import MONITOR_INTERVAL, ERROR_TIMEOUT, NETWORK_NAME, PROXY_ENDPOINTS

logger = logging.getLogger(__name__)


def run_metrics_loop():
    if NETWORK_NAME not in PROXY_ENDPOINTS:
        logger.error(f'Unsupported network: {NETWORK_NAME}')
        sys.exit(1)
    while True:
        logger.info('Metrics collector iteration started...')
        try:
            collect_metrics(NETWORK_NAME)
            logger.info(f'Metrics collector iteration done, sleeping for {MONITOR_INTERVAL}s...')
            sleep(MONITOR_INTERVAL)
        except Exception as e:
            logger.error(f'Something went wrong: {e}')
            sleep(ERROR_TIMEOUT)


if __name__ == '__main__':
    init_default_logger()
    run_metrics_loop()
