"""Fixtures a module's own tests run on, published as a pytest plugin.

The runner knows nothing about any module: it hands out the modules directory,
a node context, a loader and the requires resolution, and what is tested with
them is the module author's business.
"""

import pytest

from suil.sdk.libs.module import get_order, get_requires, load_code
from suil.workspace import Workspace

__all__ = ['get_order', 'get_requires']


@pytest.fixture(scope='session')
def workspace():
    return Workspace()


@pytest.fixture(scope='session')
def modules_dir(workspace):
    return workspace.modules_dir


@pytest.fixture(scope='session')
def suil_context():
    return {'node': 'test-01.example.com', 'role': 'test', 'family': 'redhat',
            'release': 10, 'ssh_user': 'deploy'}


@pytest.fixture(scope='session')
def load(modules_dir):
    def loader(module, part='main'):
        return load_code(module, modules_dir, part=part)

    return loader
