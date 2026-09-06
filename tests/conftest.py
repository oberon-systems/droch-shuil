import pytest

from suil.config import cfg
from suil.libs import module_load_code


@pytest.fixture(scope='session')
def modules_dir():
    return cfg.modules_dir


@pytest.fixture(scope='session')
def suil_context():
    return {'node': 'test-01.example.com', 'role': 'test', 'family': 'redhat',
            'release': 10, 'ssh_user': 'deploy'}


@pytest.fixture(scope='session')
def load(modules_dir):
    def loader(module, part='main'):
        return module_load_code(module, modules_dir, part=part)

    return loader
