import re

from pathlib import Path

SUIL_IMPORT = re.compile(r'^\s*(?:from|import)\s+(suil(?:\.\w+)*)', re.MULTILINE)
ALLOWED = ('suil.sdk', 'suil.testing')

# Not on the SDK yet: a module leaves this set in the commit that migrates it.
PENDING = {'accounts', 'amneziawg', 'awg-keeper', 'base', 'docker', 'nftables', 'nginx',
           'repos', 'ssh', 'unbound', 'xray'}


def foreign_imports(modules_dir) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}

    for path in sorted(Path(modules_dir).glob('*/**/*.py')):
        for name in SUIL_IMPORT.findall(path.read_text()):
            if not any(name == allowed or name.startswith(allowed + '.') for allowed in ALLOWED):
                module = path.relative_to(modules_dir).parts[0]
                found.setdefault(module, []).append(f'{path.relative_to(modules_dir)}: {name}')

    return found


def test_a_module_imports_suil_only_through_the_sdk_and_testing(modules_dir):
    found = foreign_imports(modules_dir)

    assert [line for module in sorted(set(found) - PENDING) for line in found[module]] == []


def test_a_migrated_module_leaves_pending(modules_dir):
    assert sorted(PENDING - set(foreign_imports(modules_dir))) == []
