"""Fixtures a module's own tests run on, published as a pytest plugin.

The runner knows nothing about any module: it hands out the modules directory,
the root of every module modules.yaml declares, a node context, a loader and
the requires resolution, and what is tested with
them is the module author's business.
"""

import pytest

from suil.sdk.libs.manifest import get_roots, read_manifest
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
def modules(workspace):
    return get_roots(read_manifest(workspace.manifest), workspace.modules_dir, workspace.cache_dir)


@pytest.fixture(scope='session')
def suil_context():
    return {'node': 'test-01.example.com', 'role': 'test', 'family': 'redhat',
            'release': 10, 'ssh_user': 'deploy'}


@pytest.fixture(scope='session')
def load(modules):
    def loader(module, part='main'):
        return load_code(modules[module], part=part)

    return loader
