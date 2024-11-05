import os
import json
import sys
import time
import logging
from datetime import datetime
from peewee import IntegrityError, OperationalError

from src.models import db, Address, TransactionCount

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_DELAY = 3
CONNECTION_TIMEOUT = 5


def wait_for_database():
    for attempt in range(MAX_RETRIES):
        try:
            db.connect(reuse_if_open=True)
            db.close()
            logger.info('Database connection successful')
            return True
        except OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f'Database connection attempt {attempt + 1} failed, '
                    f'retrying in {RETRY_DELAY} seconds... Error: {e}'
                )
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f'Failed to connect to database after {MAX_RETRIES} attempts')
                return False
    return False


def init_database():
    logger.info('Initializing test database...')

    if not wait_for_database():
        sys.exit(1)

    try:
        with db.connection_context():
            db.create_tables([Address, TransactionCount])
            logger.info('Database tables created successfully')
    except Exception as e:
        logger.error(f'Failed to create tables: {e}')
        sys.exit(1)


def load_test_data():
    data_file = os.path.join(os.path.dirname(__file__), 'test_data.json')
    try:
        with open(data_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to load test data: {e}')
        sys.exit(1)


def populate_database(test_data):
    chain_name = test_data['chain_name']
    app_name = test_data['app_name']

    for attempt in range(MAX_RETRIES):
        try:
            with db.atomic():
                for address_data in test_data['addresses']:
                    address = address_data['address']

                    try:
                        addr_record = Address.create(
                            chain_name=chain_name, address=address, app_name=app_name
                        )
                        logger.info(f'Created address record for {address}')
                    except IntegrityError:
                        logger.info(f'Address {address} already exists, skipping creation')
                        addr_record = Address.get(Address.address == address)

                    for day_data in address_data['daily_data']:
                        try:
                            TransactionCount.create(
                                address=addr_record,
                                date=datetime.strptime(day_data['date'], '%Y-%m-%d').date(),
                                total_transactions=day_data['total_transactions'],
                                daily_transactions=day_data['daily_transactions'],
                            )
                            logger.info(
                                f"Created transaction record for {address} on {day_data['date']}"
                            )
                        except IntegrityError:
                            logger.info(
                                f"Transaction record for {address} on {day_data['date']} "
                                "already exists, skipping"
                            )
            return True
        except OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f'Database population attempt {attempt + 1} failed, '
                    f'retrying in {RETRY_DELAY} seconds... Error: {e}'
                )
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f'Failed to populate database after {MAX_RETRIES} attempts')
                return False
    return False


def main():
    try:
        init_database()
        test_data = load_test_data()
        if not populate_database(test_data):
            sys.exit(1)
        logger.info('Database initialization completed successfully')
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}')
        sys.exit(1)
    finally:
        if not db.is_closed():
            db.close()


if __name__ == '__main__':
    main()
