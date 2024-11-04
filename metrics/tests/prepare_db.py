import os
import json
import sys
import logging
from datetime import datetime
from peewee import IntegrityError

from src.models import db, Address, TransactionCount

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    logger.info('Initializing test database...')

    try:
        db.connect()
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
                    logger.info(f"Created transaction record for {address} on {day_data['date']}")
                except IntegrityError:
                    logger.info(
                        f"Transaction record for {address} on {day_data['date']} already exists"
                    )


def main():
    try:
        init_database()
        test_data = load_test_data()
        populate_database(test_data)
        logger.info('Database initialization completed successfully')
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}')
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
