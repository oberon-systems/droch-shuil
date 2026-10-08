import re

from suil.sdk.errors import ModuleError
from suil.sdk.models import Root

SUIL_IMPORT = re.compile(r'^\s*(?:from|import)\s+(suil(?:\.\w+)*)')
ALLOWED = ('suil.sdk', 'suil.testing')


def check_imports(root: Root) -> None:
    """A module reaches suil only through suil.sdk and suil.testing, its tests included."""
    for path in sorted(root.path.rglob('*.py')):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not (found := SUIL_IMPORT.match(line)):
                continue

            name = found.group(1)

            if not any(name == allowed or name.startswith(allowed + '.') for allowed in ALLOWED):
                raise ModuleError(f'modules/{root.name}/{path.relative_to(root.path)}:{number} imports {name}; '
                                  f'import from suil.sdk or suil.testing instead')
