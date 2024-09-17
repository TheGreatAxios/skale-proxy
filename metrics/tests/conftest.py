import pytest
from faker import Faker

from src.metrics_types import AddressCounter


fake = Faker()

SAMPLE_APPS = {
    'app1': {'contracts': ['0x1111', '0x2222', '0x3333']},
    'app2': {'contracts': ['0x4444', '0x5555', '0x6666', '0x7777', '0x8888']},
    'app3': {'contracts': ['0x9999']},
    'app4': {'contracts': ['0xaaaa', '0xbbbb']},
    'app5': {'contracts': ['0xcccc', '0xdddd', '0xeeee', '0xffff']},
}

SAMPLE_CHAIN_INFO = {'apps': SAMPLE_APPS}

SAMPLE_METADATA = {
    'chain1': SAMPLE_CHAIN_INFO,
    'chain2': {
        'apps': {
            'app6': {'contracts': ['0x1234', '0x5678']},
            'app7': {'contracts': ['0x90ab', '0xcdef', '0x1122', '0x3344']},
        }
    },
    'chain3': {
        'apps': {
            'app8': {'contracts': ['0x5566', '0x7788', '0x99aa', '0xbbcc', '0xddee', '0xff00']},
            'app9': {'contracts': ['0x1357']},
            'app10': {'contracts': ['0x2468', '0x369c', '0x48bd']},
        }
    },
}

CHAIN_STATS = {
    'average_block_time': 5.0,
    'total_transactions': '1000000',
    'gas_price': {'average': 20.0, 'fast': 25.0, 'slow': 15.0},
}


@pytest.fixture
def sample_apps():
    return SAMPLE_APPS


@pytest.fixture
def sample_chain_info():
    return SAMPLE_CHAIN_INFO


@pytest.fixture
def sample_metadata():
    return SAMPLE_METADATA


def generate_sample_counter() -> AddressCounter:
    return {
        'gas_usage_count': str(fake.random_number(digits=5)),
        'token_transfers_count': str(fake.random_number(digits=3)),
        'transactions_count': str(fake.random_number(digits=4)),
        'validations_count': str(fake.random_number(digits=2)),
        'transactions_last_day': fake.random_int(min=0, max=100),
        'transactions_last_7_days': fake.random_int(min=0, max=500),
        'transactions_last_30_days': fake.random_int(min=0, max=2000),
    }


@pytest.fixture
def mock_chain_stats_data():
    return CHAIN_STATS
