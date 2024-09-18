import os
import json
import pytest
from faker import Faker
from aiohttp import web


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

TEST_NETWORK = 'testnet'
TEST_CHAIN = 'chain2'
TEST_ADDRESS = '0x1234'


@pytest.fixture
def sample_apps():
    return SAMPLE_APPS


@pytest.fixture
def sample_chain_info():
    return SAMPLE_CHAIN_INFO


@pytest.fixture
def sample_metadata():
    return SAMPLE_METADATA


def load_counters():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, 'counters.json')

    with open(json_file_path, 'r') as file:
        return json.load(file)


def get_latest_day_counters(counters):
    return counters['2024-09-17']


@pytest.fixture
def counters():
    return load_counters()


@pytest.fixture
def latest_day_counters():
    return get_latest_day_counters()


@pytest.fixture
def mock_chain_stats_data():
    return CHAIN_STATS


async def chain_stats_api(request):
    return web.json_response(CHAIN_STATS)


async def address_counter_api(request):
    print('request')
    address = request.match_info['address']
    if not address:
        return web.json_response({'error': 'Address parameter is required'}, status=400)

    all_counters = get_latest_day_counters(load_counters())

    for chain in all_counters.values():
        for app in chain.values():
            if address in app:
                return web.json_response(app[address])

    return web.json_response({}, status=404)


def create_app():
    app = web.Application()
    app.router.add_route('GET', '/api/v2/stats', chain_stats_api)
    app.router.add_route('GET', '/api/v2/addresses/{address}/counters', address_counter_api)
    return app


@pytest.fixture
def mock_explorer_url(monkeypatch):
    def mock_get_explorer_url(network, chain_name):
        return ''

    monkeypatch.setattr('src.explorer._get_explorer_url', mock_get_explorer_url)


@pytest.fixture
async def client(aiohttp_client):
    return await aiohttp_client(create_app())
