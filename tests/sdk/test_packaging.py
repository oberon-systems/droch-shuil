import tomllib

from pathlib import Path

import suil.sdk

ROOT = Path(suil.sdk.__file__).parent


def test_every_sdk_package_is_in_the_pyproject():
    pyproject = tomllib.loads((ROOT.parent / 'pyproject.toml').read_text())
    packages = {'.'.join(('suil', 'sdk', *init.parent.relative_to(ROOT).parts)) for init in ROOT.rglob('__init__.py')}

    assert packages - set(pyproject['tool']['setuptools']['packages']) == set()
