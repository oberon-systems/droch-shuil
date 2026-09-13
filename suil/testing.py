"""Fixtures a module's own tests run on, published as a pytest plugin.

The runner knows nothing about any module: it hands out the modules directory,
a node context and a loader, and what is tested with them is the module
author's business.
"""

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
