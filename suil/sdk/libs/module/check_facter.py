import ast
import inspect
import sys

from pathlib import Path

from suil.sdk.errors import ModuleError

from ...protocols import Collects


def check_facter(module: str, modules_dir: Path) -> None:
    """Check facts/collector.py without importing it: it runs on the node, not here.

    Standard library imports and `from suil.sdk import Facter` only, exactly one
    Facter subclass, and collect() as the Collects protocol has it.
    """
    path = Path(modules_dir) / module / 'facts' / 'collector.py'

    if not path.is_file():
        return

    source = f'modules/{module}/facts/collector.py'

    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as error:
        raise ModuleError(f'{source} does not parse: {error}') from error

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            name = '.' * node.level + (node.module or '')

            if name == 'suil.sdk' and [alias.name for alias in node.names] == ['Facter']:
                continue

            names = [name]
        else:
            continue

        for name in names:
            if name.split('.')[0] not in sys.stdlib_module_names:
                raise ModuleError(f'{source}:{node.lineno} imports {name}: standard library and suil.sdk.Facter only')

    found = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id == 'Facter' for base in node.bases)
    ]

    if len(found) != 1:
        names = ', '.join(sorted(node.name for node in found)) or 'none'
        raise ModuleError(f'{source} must declare exactly one Facter subclass, found: {names}')

    cls = found[0]
    collect = next((node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'collect'), None)

    if collect is None:
        raise ModuleError(f'{source}: {cls.name} does not override collect()')

    expected = str(inspect.signature(Collects.collect))
    actual = f'({ast.unparse(collect.args)})' + (f' -> {ast.unparse(collect.returns)}' if collect.returns else '')

    if actual != expected:
        raise ModuleError(f'{source}: {cls.name}.collect{actual} must be collect{expected}')
