import importlib

from pathlib import Path

import pytest

import suil.sdk

ROOT = Path(suil.sdk.__file__).parent
FILES = sorted(path for path in ROOT.rglob('*.py') if '__pycache__' not in path.parts)


def dotted(path: Path) -> str:
    parts = path.relative_to(ROOT).with_suffix('').parts

    return '.'.join(('suil', 'sdk', *(parts[:-1] if parts[-1] == '__init__' else parts)))


@pytest.mark.parametrize('name', [dotted(path) for path in FILES])
def test_every_file_imports_and_every_export_resolves(name):
    package = importlib.import_module(name)

    for export in getattr(package, '__all__', []):
        assert getattr(package, export, None) is not None, f'{name}.{export}'
